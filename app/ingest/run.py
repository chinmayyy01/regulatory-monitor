import argparse
import gzip
import hashlib
import time
from datetime import date
from pathlib import Path

import requests
from psycopg.types.json import Jsonb

from app.db import apply_schema, connect
from app.fetchers.base import request_bytes
from app.ingest.html_doc import (
    paragraphs_to_clauses,
    rbi_paragraphs,
    rbi_pdf_url,
    sebi_pdf_url,
)
from app.ingest.pdf import parse_pdf
from app.ingest.segment import Clause, segment
from app.ingest.source import fetch_month, fetch_sebi_listing, iter_months

RAW_DIR = Path("data/raw")

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


def save_payload(payload: bytes) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{digest}.gz"
    if not path.exists():
        path.write_bytes(gzip.compress(payload))
    return digest


def store_document(
    connection,
    *,
    url: str,
    title: str,
    date_issued: date | None,
    clauses: list[Clause],
    payload: bytes,
    pdf_url: str | None = None,
    page_count: int = 0,
    dry_run: bool = False,
) -> bool:
    digest = hashlib.sha256(payload).hexdigest()
    if connection.execute(DOC_EXISTS, (url, digest)).fetchone():
        return False
    if dry_run:
        print(f"  would store: {title[:60]} | {len(clauses)} clauses", flush=True)
        return True

    save_payload(payload)
    row = connection.execute(
        INSERT_DOC,
        (url, title, classify(title), date_issued, pdf_url, digest, page_count),
    ).fetchone()
    if row is None:
        connection.commit()
        return False

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
    return True


def fetch_pdf(session, url: str) -> bytes | None:
    for delay in (0, 2, 6):
        if delay:
            time.sleep(delay)
        try:
            data = request_bytes("GET", url, session=session, timeout=60)
        except Exception:
            continue
        if data.startswith(b"%PDF"):
            return data
    return None


def ingest_rbi_month(connection, session, year: int, month: int, args) -> int:
    announcements = fetch_month(session, year, month)
    print(f"[rbi {year}-{month:02d}] {len(announcements)} announcements", flush=True)

    stored = 0
    for item in announcements:
        try:
            html = request_bytes("GET", item.detail_url, session=session, timeout=30)
        except Exception as error:
            print(f"  detail failed: {item.detail_url}: {error}", flush=True)
            continue

        paragraphs = rbi_paragraphs(html)
        if not paragraphs:
            print(f"  no text: {item.title[:60]}", flush=True)
            continue

        inserted = store_document(
            connection,
            url=item.detail_url,
            title=item.title,
            date_issued=item.date_issued,
            clauses=paragraphs_to_clauses(paragraphs),
            payload=html,
            pdf_url=rbi_pdf_url(html),
            dry_run=args.dry_run,
        )
        if inserted:
            stored += 1
            print(f"  + {item.title[:58]} | {len(paragraphs)} paras", flush=True)
        if args.limit and stored >= args.limit:
            return stored
        time.sleep(args.sleep)

    return stored


def ingest_sebi(connection, session, args) -> int:
    announcements = fetch_sebi_listing(session)
    print(f"[sebi] {len(announcements)} recent circulars", flush=True)

    stored = 0
    for item in announcements:
        try:
            html = request_bytes("GET", item.detail_url, session=session, timeout=30)
        except Exception as error:
            print(f"  detail failed: {item.detail_url}: {error}", flush=True)
            continue

        pdf_url = sebi_pdf_url(html)
        if pdf_url is None:
            print(f"  no pdf: {item.title[:60]}", flush=True)
            continue

        pdf = fetch_pdf(session, pdf_url)
        if pdf is None:
            print(f"  pdf unavailable: {pdf_url}", flush=True)
            continue

        lines, pages = parse_pdf(pdf)
        inserted = store_document(
            connection,
            url=item.detail_url,
            title=item.title,
            date_issued=item.date_issued,
            clauses=segment(lines),
            payload=html,
            pdf_url=pdf_url,
            page_count=pages,
            dry_run=args.dry_run,
        )
        if inserted:
            stored += 1
            print(f"  + {item.title[:58]} | {pages}p", flush=True)
        if args.limit and stored >= args.limit:
            return stored
        time.sleep(args.sleep)

    return stored


def ingest_directory(connection, directory: Path, args) -> int:
    imported = 0
    for path in sorted(directory.glob("*.pdf")):
        pdf_bytes = path.read_bytes()
        lines, pages = parse_pdf(pdf_bytes)
        inserted = store_document(
            connection,
            url=f"local:{path.name}",
            title=path.stem,
            date_issued=None,
            clauses=segment(lines),
            payload=pdf_bytes,
            page_count=pages,
            dry_run=args.dry_run,
        )
        if inserted:
            imported += 1
            print(f"  + {path.name} | {pages}p", flush=True)
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description="Load RBI and SEBI circulars into Postgres")
    parser.add_argument("--source", choices=["all", "rbi", "sebi", "dir"], default="all")
    parser.add_argument("--start", default="2023-01", help="first month for RBI, YYYY-MM")
    parser.add_argument("--end", default=date.today().strftime("%Y-%m"), help="last month for RBI")
    parser.add_argument("--limit", type=int, default=0, help="stop after N documents (0 = all)")
    parser.add_argument("--sleep", type=float, default=1.5, help="seconds between requests")
    parser.add_argument("--dry-run", action="store_true", help="parse but do not write")
    parser.add_argument("--dir", default=None, help="import every *.pdf in this folder")
    args = parser.parse_args()

    connection = connect()
    apply_schema(connection)
    session = requests.Session()
    total = 0

    if args.source == "dir":
        if not args.dir:
            raise SystemExit("--source dir needs --dir PATH")
        total = ingest_directory(connection, Path(args.dir), args)

    if args.source in ("all", "rbi"):
        for year, month in iter_months(parse_month(args.start), parse_month(args.end)):
            try:
                total += ingest_rbi_month(connection, session, year, month, args)
            except Exception as error:
                connection.rollback()
                print(f"[rbi {year}-{month:02d}] month failed: {error}", flush=True)
            if args.limit and total >= args.limit:
                break

    if args.source in ("all", "sebi"):
        try:
            total += ingest_sebi(connection, session, args)
        except Exception as error:
            connection.rollback()
            print(f"[sebi] failed: {error}", flush=True)

    print(f"done: {total} documents stored")
    connection.close()


if __name__ == "__main__":
    main()
