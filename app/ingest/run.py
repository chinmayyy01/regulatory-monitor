import argparse
import hashlib
import time
from datetime import date
from pathlib import Path

import requests
from psycopg.types.json import Jsonb

from app.db import apply_schema, connect
from app.fetchers.base import request_bytes
from app.ingest.pdf import parse_pdf
from app.ingest.segment import segment
from app.ingest.source import fetch_month, iter_months

PDF_DIR = Path("data/pdfs")

DOC_EXISTS = "SELECT 1 FROM reg_doc WHERE url = %s OR sha256 = %s"

INSERT_DOC = """
INSERT INTO reg_doc (url, title, doc_type, date_issued, pdf_url, sha256, page_count)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT DO NOTHING
RETURNING id
"""

INSERT_CLAUSE = """
INSERT INTO reg_clause (reg_doc_id, ordinal, section_no, heading_path, text, page, bbox, spans)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


class PdfBlocked(RuntimeError):
    pass


def download_pdf(session, url: str) -> bytes:
    for delay in (0, 2, 6):
        if delay:
            time.sleep(delay)
        data = request_bytes(
            "GET",
            url,
            session=session,
            headers={
                "Referer": "https://www.rbi.org.in/",
                "Accept": "application/pdf,*/*",
            },
            timeout=60,
        )
        if data.startswith(b"%PDF"):
            return data
    raise PdfBlocked(url)


def classify(title: str) -> str:
    lowered = title.lower()
    if lowered.startswith("master direction"):
        return "master_direction"
    if "directions" in lowered:
        return "directions"
    if "circular" in lowered:
        return "circular"
    return "notification"


def parse_month(value: str) -> tuple[int, int]:
    year, month = value.split("-")
    return int(year), int(month)


def save_pdf(sha256: str, data: bytes) -> Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / f"{sha256}.pdf"
    if not path.exists():
        path.write_bytes(data)
    return path


def ingest_month(connection, session, year: int, month: int, args) -> int:
    announcements = fetch_month(session, year, month)
    print(f"[{year}-{month:02d}] {len(announcements)} announcements", flush=True)

    inserted = 0
    for item in announcements:
        if item.pdf_url is None:
            print(f"  skip (no pdf): {item.title[:60]}", flush=True)
            continue

        existing = connection.execute(DOC_EXISTS, (item.detail_url, "")).fetchone()
        if existing:
            continue

        try:
            pdf_bytes = download_pdf(session, item.pdf_url)
        except PdfBlocked:
            raise
        except Exception as error:
            print(f"  fetch failed: {item.pdf_url}: {error}", flush=True)
            continue

        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        if connection.execute(DOC_EXISTS, (item.detail_url, sha256)).fetchone():
            continue

        lines, total_pages = parse_pdf(pdf_bytes)
        clauses = segment(lines)

        if args.dry_run:
            print(f"  would insert: {item.title[:60]} | {len(clauses)} clauses", flush=True)
            inserted += 1
        else:
            save_pdf(sha256, pdf_bytes)
            row = connection.execute(
                INSERT_DOC,
                (
                    item.detail_url,
                    item.title,
                    classify(item.title),
                    item.date_issued,
                    item.pdf_url,
                    sha256,
                    total_pages,
                ),
            ).fetchone()
            if row is None:
                connection.commit()
                continue
            doc_id = row[0]
            for clause in clauses:
                connection.execute(
                    INSERT_CLAUSE,
                    (
                        doc_id,
                        clause.ordinal,
                        clause.section_no,
                        clause.heading_path,
                        clause.text,
                        clause.page,
                        Jsonb(clause.bbox),
                        Jsonb(clause.spans),
                    ),
                )
            connection.commit()
            inserted += 1
            print(
                f"  + {item.title[:58]} | {len(clauses)} clauses "
                f"| {item.date_issued} | {classify(item.title)}",
                flush=True,
            )

        if args.limit and inserted >= args.limit:
            return inserted
        time.sleep(args.sleep)

    return inserted


def ingest_directory(connection, directory: Path) -> int:
    imported = 0
    for path in sorted(directory.glob("*.pdf")):
        pdf_bytes = path.read_bytes()
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()
        source_url = f"local:{path.name}"
        if connection.execute(DOC_EXISTS, (source_url, sha256)).fetchone():
            print(f"  skip (already imported): {path.name}", flush=True)
            continue

        lines, total_pages = parse_pdf(pdf_bytes)
        clauses = segment(lines)
        save_pdf(sha256, pdf_bytes)
        row = connection.execute(
            INSERT_DOC,
            (
                source_url,
                path.stem,
                classify(path.stem),
                None,
                None,
                sha256,
                total_pages,
            ),
        ).fetchone()
        if row is None:
            connection.commit()
            continue
        doc_id = row[0]
        for clause in clauses:
            connection.execute(
                INSERT_CLAUSE,
                (
                    doc_id,
                    clause.ordinal,
                    clause.section_no,
                    clause.heading_path,
                    clause.text,
                    clause.page,
                    Jsonb(clause.bbox),
                    Jsonb(clause.spans),
                ),
            )
        connection.commit()
        imported += 1
        print(f"  + {path.name} | {total_pages}p | {len(clauses)} clauses", flush=True)

    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Load RBI circulars into Postgres")
    parser.add_argument("--start", default="2023-01", help="first month, YYYY-MM")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m"), help="last month, YYYY-MM")
    parser.add_argument("--limit", type=int, default=0, help="stop after N documents (0 = all)")
    parser.add_argument("--sleep", type=float, default=1.5, help="seconds between downloads")
    parser.add_argument("--dry-run", action="store_true", help="parse but do not write")
    parser.add_argument("--dir", default=None, help="import every *.pdf in this folder instead of scraping")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)

    if args.dir:
        imported = ingest_directory(connection, Path(args.dir))
        print(f"done: {imported} documents imported from {args.dir}")
        connection.close()
        return

    start = parse_month(args.start)
    end = parse_month(args.end)
    session = requests.Session()

    total = 0
    for year, month in iter_months(start, end):
        try:
            total += ingest_month(connection, session, year, month, args)
        except PdfBlocked as error:
            print(
                f"stopped: RBI returned a bot-check page instead of a PDF ({error}).\n"
                "wait a while before retrying; do not lower --sleep.",
                flush=True,
            )
            break
        except Exception as error:
            connection.rollback()
            print(f"[{year}-{month:02d}] month failed: {error}", flush=True)
        if args.limit and total >= args.limit:
            break

    print(f"done: {total} documents inserted")
    connection.close()


if __name__ == "__main__":
    main()
