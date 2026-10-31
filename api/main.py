import hashlib
import os
import time
from types import SimpleNamespace
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from app.auth.audit import clear_failures, recent_failures, record_attempt, record_event
from app.auth.passwords import verify_password
from app.auth.sessions import (
    create_session,
    delete_session,
    list_sessions,
    revoke_all,
    revoke_session,
    user_for_token,
)
from app.chat.answer import ask as answer_question
from app.config import MODEL_WORKER
from app.ingest.pdf import parse_pdf
from app.ingest.segment import segment
from app.mapping.run import run as run_mapping
from app.tenant.ingest import embed_pending, store_document
from app.chat.retrieve import gather
from app.db import apply_schema, connect, connect_app

MAX_FAILURES = 5


@asynccontextmanager
async def lifespan(_app):
    if not os.getenv("DATABASE_URL_APP", "").strip():
        raise RuntimeError(
            "DATABASE_URL_APP is required: the API must connect as a non-superuser role "
            "so row-level security applies. See sql/007_rls.sql."
        )
    with connect() as connection:
        apply_schema(connection)
    yield


app = FastAPI(title="RegIntel API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

LATEST_RUN = """
SELECT run_id FROM mapping
WHERE tenant_id = %s
GROUP BY run_id
ORDER BY max(created_at) DESC
LIMIT 1
"""

TENANTS = """
SELECT t.id, t.name, t.entity_type, t.license_type, t.products,
       (SELECT count(*) FROM tenant_doc d WHERE d.tenant_id = t.id) AS documents,
       (SELECT count(*) FROM tenant_clause c
          JOIN tenant_doc d2 ON d2.id = c.tenant_doc_id
         WHERE d2.tenant_id = t.id) AS clauses
FROM tenant t
WHERE t.id = %s
"""

GAPS = """
SELECT m.obligation_id, o.action, o.condition, o.modality,
       m.verdict, m.confidence,
       m.evidence_regulation, m.evidence_policy, m.reason,
       tc.text AS clause_text, tc.section_no, td.title AS document_title
FROM mapping m
JOIN obligation o ON o.id = m.obligation_id
LEFT JOIN tenant_clause tc ON tc.id = m.tenant_clause_id
LEFT JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE m.tenant_id = %s AND m.run_id = %s
ORDER BY CASE m.verdict
             WHEN 'missing' THEN 0
             WHEN 'stale' THEN 1
             WHEN 'partial' THEN 2
             ELSE 3
         END,
         m.id
LIMIT %s
"""

SUMMARY = """
SELECT m.verdict, count(*)
FROM mapping m
WHERE m.tenant_id = %s AND m.run_id = %s
GROUP BY m.verdict
"""

USER_LOGIN = "SELECT id, email, password_hash, tenant_id, role FROM app_user WHERE email = %s"

DOCUMENTS = """
SELECT d.id, d.title, d.doc_type, d.version, d.effective_from, d.page_count, d.created_at,
       (SELECT count(*) FROM tenant_clause c WHERE c.tenant_doc_id = d.id) AS clauses
FROM tenant_doc d
WHERE d.tenant_id = %s
ORDER BY d.created_at DESC
"""

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class Tenant(BaseModel):
    id: int
    name: str
    entity_type: str
    license_type: str | None
    products: list[str]
    documents: int
    clauses: int


class Gap(BaseModel):
    obligation_id: int
    action: str
    condition: str
    modality: str
    verdict: str
    confidence: float
    evidence_regulation: str
    evidence_policy: str
    reason: str
    clause_text: str | None
    section_no: str | None
    document_title: str | None


class GapsResponse(BaseModel):
    tenant_id: int
    run_id: str | None
    summary: dict[str, int]
    gaps: list[Gap]


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    as_of: date | None = None


class Citation(BaseModel):
    kind: Literal["regulation", "policy"]
    clause_id: int
    label: str
    quote: str
    span: dict


class Claim(BaseModel):
    text: str
    citations: list[Citation]


class AskResponse(BaseModel):
    question: str
    insufficient: bool
    rejected: int
    claims: list[Claim]


class Document(BaseModel):
    id: int
    title: str
    doc_type: str
    version: str | None
    effective_from: date | None
    page_count: int
    clauses: int
    created_at: str


class UploadResponse(BaseModel):
    document_id: int
    title: str
    clauses: int
    pages: int


class MapResponse(BaseModel):
    run_id: str | None
    mapped: int
    rejected: int
    applicable: int


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class SessionUser(BaseModel):
    id: int
    email: str
    tenant_id: int
    role: str


class LoginResponse(BaseModel):
    token: str
    user: SessionUser


def token_from_header(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_user(authorization: str | None = Header(default=None)) -> SessionUser:
    token = token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not signed in")
    with connect_app() as connection:
        row = user_for_token(connection, token)
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session expired")
    return SessionUser(id=row[0], email=row[1], tenant_id=row[2], role=row[3])


def require_owner(user: SessionUser = Depends(require_user)) -> SessionUser:
    if user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")
    return user


def require_tenant(user: SessionUser, tenant_id: int) -> None:
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your tenant")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: Credentials, request: Request) -> LoginResponse:
    email = credentials.email.lower().strip()
    ip = client_ip(request)
    agent = request.headers.get("user-agent", "")

    with connect_app() as connection:
        if recent_failures(connection, email) >= MAX_FAILURES:
            record_event(connection, "login_locked", email=email, ip=ip, user_agent=agent)
            raise HTTPException(status_code=429, detail="too many attempts, try again later")

        row = connection.execute(USER_LOGIN, (email,)).fetchone()
        if row is None or not verify_password(credentials.password, row[2]):
            record_attempt(connection, email, ip, False)
            record_event(
                connection,
                "login_failure",
                user_id=row[0] if row else None,
                email=email,
                ip=ip,
                user_agent=agent,
            )
            raise HTTPException(status_code=401, detail="invalid email or password")

        record_attempt(connection, email, ip, True)
        clear_failures(connection, email)
        token = create_session(connection, row[0], agent)
        record_event(connection, "login_success", user_id=row[0], email=email, ip=ip, user_agent=agent)

    return LoginResponse(
        token=token,
        user=SessionUser(id=row[0], email=row[1], tenant_id=row[3], role=row[4]),
    )


@app.post("/api/auth/logout")
def logout(request: Request, authorization: str | None = Header(default=None)) -> dict:
    token = token_from_header(authorization)
    if token:
        with connect_app() as connection:
            row = user_for_token(connection, token)
            delete_session(connection, token)
            if row is not None:
                record_event(
                    connection,
                    "logout",
                    user_id=row[0],
                    email=row[1],
                    ip=client_ip(request),
                    user_agent=request.headers.get("user-agent", ""),
                )
    return {"status": "signed out"}


@app.post("/api/auth/logout-all")
def logout_all(request: Request, user: SessionUser = Depends(require_user)) -> dict:
    with connect_app() as connection:
        removed = revoke_all(connection, user.id)
        record_event(
            connection,
            "logout_all",
            user_id=user.id,
            email=user.email,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    return {"revoked": removed}


@app.get("/api/auth/sessions")
def sessions(user: SessionUser = Depends(require_user)) -> list[dict]:
    with connect_app() as connection:
        rows = list_sessions(connection, user.id)
    return [
        {
            "id": row[0],
            "created_at": row[1].isoformat(),
            "expires_at": row[2].isoformat(),
            "user_agent": row[3],
        }
        for row in rows
    ]


@app.delete("/api/auth/sessions/{session_id}")
def revoke_one(
    session_id: int,
    request: Request,
    user: SessionUser = Depends(require_user),
) -> dict:
    with connect_app() as connection:
        removed = revoke_session(connection, user.id, session_id)
        if removed:
            record_event(
                connection,
                "session_revoke",
                user_id=user.id,
                email=user.email,
                ip=client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
            )
    return {"revoked": removed}


@app.get("/api/auth/me", response_model=SessionUser)
def me(user: SessionUser = Depends(require_user)) -> SessionUser:
    return user


@app.get("/api/tenants", response_model=list[Tenant])
def tenants(user: SessionUser = Depends(require_user)) -> list[Tenant]:
    with connect_app(user.tenant_id) as connection:
        rows = connection.execute(TENANTS, (user.tenant_id,)).fetchall()
    return [
        Tenant(
            id=row[0],
            name=row[1],
            entity_type=row[2],
            license_type=row[3],
            products=row[4] or [],
            documents=row[5],
            clauses=row[6],
        )
        for row in rows
    ]


@app.get("/api/tenants/{tenant_id}/documents", response_model=list[Document])
def documents(tenant_id: int, user: SessionUser = Depends(require_user)) -> list[Document]:
    require_tenant(user, tenant_id)
    with connect_app(user.tenant_id) as connection:
        rows = connection.execute(DOCUMENTS, (tenant_id,)).fetchall()
    return [
        Document(
            id=row[0],
            title=row[1],
            doc_type=row[2],
            version=row[3],
            effective_from=row[4],
            page_count=row[5],
            clauses=row[7],
            created_at=row[6].isoformat(),
        )
        for row in rows
    ]


@app.post("/api/tenants/{tenant_id}/documents", response_model=UploadResponse, status_code=201)
async def upload_document(
    tenant_id: int,
    file: UploadFile = File(...),
    user: SessionUser = Depends(require_owner),
) -> UploadResponse:
    require_tenant(user, tenant_id)

    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file is larger than 10 MB")
    if not payload.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="only PDF files are accepted")

    name = (file.filename or "policy.pdf").rsplit("/", 1)[-1]
    title = name.removesuffix(".pdf").replace("_", " ").replace("-", " ").title() or "Policy"

    try:
        lines, pages = parse_pdf(payload)
    except Exception:
        raise HTTPException(status_code=400, detail="could not parse that PDF") from None
    if not lines:
        raise HTTPException(status_code=400, detail="that PDF has no extractable text")

    digest = hashlib.sha256(payload).hexdigest()

    with connect_app(user.tenant_id) as connection:
        document_id = store_document(
            connection,
            tenant_id,
            title,
            "policy",
            segment(lines),
            digest,
            pages,
        )
        if document_id is None:
            raise HTTPException(status_code=409, detail="this document is already uploaded")
        embed_pending(connection, tenant_id)
        clause_count = connection.execute(
            "SELECT count(*) FROM tenant_clause WHERE tenant_doc_id = %s", (document_id,)
        ).fetchone()[0]

    return UploadResponse(document_id=document_id, title=title, clauses=clause_count, pages=pages)


@app.post("/api/tenants/{tenant_id}/map", response_model=MapResponse)
def map_tenant(
    tenant_id: int,
    limit: int = 10,
    user: SessionUser = Depends(require_owner),
) -> MapResponse:
    require_tenant(user, tenant_id)

    with connect_app(user.tenant_id) as connection:
        name = connection.execute("SELECT name FROM tenant WHERE id = %s", (tenant_id,)).fetchone()[0]
        options = SimpleNamespace(
            limit=max(1, min(limit, 25)),
            candidates=5,
            sleep=0.2,
            dry_run=False,
            ids=None,
            model=MODEL_WORKER,
        )
        mapped, rejected, applicable = run_mapping(connection, name, options)
        run_id = connection.execute(LATEST_RUN, (tenant_id,)).fetchone()

    return MapResponse(
        run_id=run_id[0] if run_id else None,
        mapped=mapped,
        rejected=rejected,
        applicable=applicable,
    )


@app.get("/api/tenants/{tenant_id}/gaps", response_model=GapsResponse)
def gaps(
    tenant_id: int,
    limit: int = 100,
    user: SessionUser = Depends(require_user),
) -> GapsResponse:
    require_tenant(user, tenant_id)

    with connect_app(user.tenant_id) as connection:
        run = connection.execute(LATEST_RUN, (tenant_id,)).fetchone()
        if run is None:
            return GapsResponse(tenant_id=tenant_id, run_id=None, summary={}, gaps=[])
        run_id = run[0]
        summary = {
            verdict: count
            for verdict, count in connection.execute(SUMMARY, (tenant_id, run_id)).fetchall()
        }
        rows = connection.execute(GAPS, (tenant_id, run_id, min(limit, 500))).fetchall()

    return GapsResponse(
        tenant_id=tenant_id,
        run_id=run_id,
        summary=summary,
        gaps=[
            Gap(
                obligation_id=row[0],
                action=row[1],
                condition=row[2] or "",
                modality=row[3],
                verdict=row[4],
                confidence=row[5],
                evidence_regulation=row[6] or "",
                evidence_policy=row[7] or "",
                reason=row[8] or "",
                clause_text=row[9],
                section_no=row[10],
                document_title=row[11],
            )
            for row in rows
        ],
    )


@app.post("/api/tenants/{tenant_id}/ask", response_model=AskResponse)
def ask(
    tenant_id: int,
    request: AskRequest,
    user: SessionUser = Depends(require_user),
) -> AskResponse:
    require_tenant(user, tenant_id)

    with connect_app(user.tenant_id) as connection:
        sources = gather(connection, tenant_id, request.question, request.as_of)

    answer = answer_question(request.question, sources)
    return AskResponse(
        question=request.question,
        insufficient=answer.insufficient,
        rejected=answer.rejected,
        claims=[
            Claim(
                text=claim.text,
                citations=[
                    Citation(
                        kind=citation.kind,
                        clause_id=citation.clause_id,
                        label=citation.label,
                        quote=citation.quote,
                        span=citation.span,
                    )
                    for citation in claim.citations
                ],
            )
            for claim in answer.claims
        ],
    )
