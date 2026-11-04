import hashlib
import os
import secrets
from pathlib import Path
import time
from types import SimpleNamespace
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from app.auth.accounts import EmailTaken, WorkspaceTaken, create_account
from app.auth.passwords import hash_password
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
from app.change.feed import OBLIGATION_TEXT, RUNS, VERDICTS, diff, verdict_map
from app.chat.answer import ask as answer_question
from app.config import MODEL_WORKER
from app.ingest.pdf import parse_pdf
from app.ingest.segment import segment
from app.mapping.run import run as run_mapping
from app.tenant.ingest import embed_pending, store_document
from app.chat.retrieve import gather
from app.jobs import run_map_job, start as start_job
from app.db import apply_schema, connect, connect_app

MAX_FAILURES = 5
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "").strip().lower() in ("1", "true", "yes")
SIGNUP_LIMIT = 5
SIGNUP_WINDOW_SECONDS = 3600
_signups: dict[str, list[float]] = {}


def signup_allowed(ip: str) -> bool:
    now = time.time()
    recent = [stamp for stamp in _signups.get(ip, []) if now - stamp < SIGNUP_WINDOW_SECONDS]
    if len(recent) >= SIGNUP_LIMIT:
        _signups[ip] = recent
        return False
    recent.append(now)
    _signups[ip] = recent
    return True


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
       tc.text AS clause_text, tc.section_no, td.title AS document_title,
       m.policy_span, tc.page, td.id
FROM mapping m
JOIN obligation o ON o.id = m.obligation_id
LEFT JOIN tenant_clause tc ON tc.id = m.tenant_clause_id
LEFT JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE m.tenant_id = %s AND m.run_id = %s
ORDER BY CASE m.verdict
             WHEN 'satisfied' THEN 0
             WHEN 'partial' THEN 1
             WHEN 'stale' THEN 2
             ELSE 3
         END,
         m.confidence DESC,
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
    policy_span: dict | None
    page: int | None
    document_id: int | None


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
    unsupported: int
    claims: list[Claim]


class NewTenant(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    entity_type: str = Field(min_length=2, max_length=40)
    products: list[str] = Field(default_factory=list)


class Membership(BaseModel):
    tenant_id: int
    name: str
    role: str


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


class MapJob(BaseModel):
    job_id: int
    status: str


class JobStatus(BaseModel):
    job_id: int
    status: str
    mapped: int
    detail: str


class OAuthExchange(BaseModel):
    email: EmailStr
    name: str = ""


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    workspace: str = Field(min_length=2, max_length=60)
    entity_type: str = Field(default="nbfc", min_length=2, max_length=40)


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


def default_session_user() -> SessionUser:
    with connect_app() as connection:
        user = connection.execute(
            "SELECT id, email, tenant_id, role FROM app_user WHERE role = 'owner' ORDER BY id LIMIT 1"
        ).fetchone()
        if user is not None:
            return SessionUser(id=user[0], email=user[1], tenant_id=user[2], role=user[3])
        row = connection.execute(
            "SELECT id FROM tenant ORDER BY id LIMIT 1"
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=503, detail="no tenant exists; run make demo")
    return SessionUser(id=0, email="demo@localhost", tenant_id=row[0], role="owner")


def require_user(authorization: str | None = Header(default=None)) -> SessionUser:
    if AUTH_DISABLED:
        return default_session_user()

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
    if AUTH_DISABLED:
        return
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your tenant")
    with connect_app(user.tenant_id) as connection:
        row = connection.execute(
            "SELECT 1 FROM membership WHERE user_id = %s AND tenant_id = %s",
            (user.id, tenant_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no access to tenant")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "auth_disabled": AUTH_DISABLED}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@app.post("/api/auth/oauth/exchange", response_model=LoginResponse)
def oauth_exchange(
    payload: OAuthExchange,
    request: Request,
    x_oauth_secret: str | None = Header(default=None, alias="X-OAuth-Secret"),
) -> LoginResponse:
    expected = os.getenv("OAUTH_SHARED_SECRET", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="OAuth is not configured on the API")
    if not x_oauth_secret or x_oauth_secret != expected:
        raise HTTPException(status_code=401, detail="bad exchange secret")

    email = payload.email.lower().strip()
    agent = request.headers.get("user-agent", "")

    with connect_app() as connection:
        row = connection.execute(
            "SELECT id, email, tenant_id, role FROM app_user WHERE email = %s", (email,)
        ).fetchone()
        created = False

        if row is None:
            domain = email.split("@")[-1] or "workspace"
            base_name = domain
            suffix = 1
            while connection.execute(
                "SELECT 1 FROM tenant WHERE name = %s", (base_name,)
            ).fetchone():
                suffix += 1
                base_name = f"{domain} {suffix}"

            tenant = connection.execute(
                "INSERT INTO tenant (name, entity_type, products) VALUES (%s, 'nbfc', %s) RETURNING id",
                (base_name, ["lending"]),
            ).fetchone()
            unusable = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
            row = connection.execute(
                """
                INSERT INTO app_user (email, password_hash, tenant_id)
                VALUES (%s, %s, %s)
                RETURNING id, email, tenant_id, role
                """,
                (email, hash_password(unusable), tenant[0]),
            ).fetchone()
            connection.execute(
                "INSERT INTO membership (user_id, tenant_id, role) VALUES (%s, %s, 'owner') "
                "ON CONFLICT DO NOTHING",
                (row[0], tenant[0]),
            )
            connection.commit()
            created = True

        token = create_session(connection, row[0], agent)
        record_event(
            connection,
            "oauth_login" if not created else "oauth_signup",
            user_id=row[0],
            email=row[1],
            ip=client_ip(request),
            user_agent=agent,
        )

    return LoginResponse(
        token=token,
        user=SessionUser(id=row[0], email=row[1], tenant_id=row[2], role=row[3]),
    )


@app.post("/api/auth/signup", response_model=LoginResponse, status_code=201)
def signup(payload: SignupRequest, request: Request) -> LoginResponse:
    ip = client_ip(request)
    if not signup_allowed(ip):
        raise HTTPException(status_code=429, detail="too many accounts from this address, try later")

    agent = request.headers.get("user-agent", "")
    try:
        with connect_app() as connection:
            user = create_account(
                connection,
                payload.email,
                payload.password,
                payload.workspace,
                payload.entity_type,
            )
            token = create_session(connection, user[0], agent)
            record_event(connection, "signup", user_id=user[0], email=user[1], ip=ip, user_agent=agent)
    except EmailTaken:
        raise HTTPException(status_code=409, detail="an account with that email already exists") from None
    except WorkspaceTaken:
        raise HTTPException(status_code=409, detail="that workspace name is already taken") from None
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None

    return LoginResponse(
        token=token,
        user=SessionUser(id=user[0], email=user[1], tenant_id=user[2], role=user[3]),
    )


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


class ObligationDetail(BaseModel):
    obligation_id: int
    action: str
    condition: str
    modality: str
    scope_entities: list[str]
    valid_from: date | None
    regulation_clause_id: int
    regulation_text: str
    regulation_section: str | None
    regulation_page: int | None
    regulation_title: str
    verdict: str | None
    confidence: float | None
    evidence_regulation: str
    evidence_policy: str
    reason: str
    policy_clause_id: int | None
    policy_text: str | None
    policy_section: str | None
    policy_page: int | None
    policy_title: str | None
    policy_span: dict | None
    policy_document_id: int | None


class Change(BaseModel):
    obligation_id: int
    before: str | None
    after: str | None
    direction: str
    action: str


class ChangesResponse(BaseModel):
    from_run: str | None
    to_run: str | None
    changes: list[Change]


OBLIGATION_DETAIL = """
SELECT o.id, o.action, o.condition, o.modality, o.scope_entities, o.valid_from,
       rc.id, rc.text, rc.section_no, rc.page, rd.title
FROM obligation o
JOIN reg_clause rc ON rc.id = o.reg_clause_id
JOIN reg_doc rd ON rd.id = rc.reg_doc_id
WHERE o.id = %s
"""

LATEST_MAPPING = """
SELECT m.verdict, m.confidence, m.evidence_regulation, m.evidence_policy, m.reason,
       m.policy_span, tc.id, tc.text, tc.section_no, tc.page, td.id, td.title
FROM mapping m
LEFT JOIN tenant_clause tc ON tc.id = m.tenant_clause_id
LEFT JOIN tenant_doc td ON td.id = tc.tenant_doc_id
WHERE m.tenant_id = %s AND m.obligation_id = %s
ORDER BY m.created_at DESC
LIMIT 1
"""


@app.get("/api/tenants/{tenant_id}/obligations/{obligation_id}", response_model=ObligationDetail)
def obligation_detail(
    tenant_id: int,
    obligation_id: int,
    user: SessionUser = Depends(require_user),
) -> ObligationDetail:
    require_tenant(user, tenant_id)

    with connect_app(user.tenant_id) as connection:
        row = connection.execute(OBLIGATION_DETAIL, (obligation_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="obligation not found")
        mapping = connection.execute(LATEST_MAPPING, (tenant_id, obligation_id)).fetchone()

    return ObligationDetail(
        obligation_id=row[0],
        action=row[1],
        condition=row[2] or "",
        modality=row[3],
        scope_entities=row[4] or [],
        valid_from=row[5],
        regulation_clause_id=row[6],
        regulation_text=row[7],
        regulation_section=row[8],
        regulation_page=row[9],
        regulation_title=row[10],
        verdict=mapping[0] if mapping else None,
        confidence=mapping[1] if mapping else None,
        evidence_regulation=(mapping[2] or "") if mapping else "",
        evidence_policy=(mapping[3] or "") if mapping else "",
        reason=(mapping[4] or "") if mapping else "",
        policy_span=mapping[5] if mapping else None,
        policy_clause_id=mapping[6] if mapping else None,
        policy_text=mapping[7] if mapping else None,
        policy_section=mapping[8] if mapping else None,
        policy_page=mapping[9] if mapping else None,
        policy_document_id=mapping[10] if mapping else None,
        policy_title=mapping[11] if mapping else None,
    )


@app.get("/api/tenants/{tenant_id}/changes", response_model=ChangesResponse)
def changes(tenant_id: int, user: SessionUser = Depends(require_user)) -> ChangesResponse:
    require_tenant(user, tenant_id)
    with connect_app(user.tenant_id) as connection:
        runs = connection.execute(RUNS, (tenant_id, 2)).fetchall()
        if len(runs) < 2:
            return ChangesResponse(from_run=None, to_run=None, changes=[])
        to_run, from_run = runs[0][0], runs[1][0]
        old = verdict_map(connection.execute(VERDICTS, (tenant_id, from_run)).fetchall())
        new = verdict_map(connection.execute(VERDICTS, (tenant_id, to_run)).fetchall())
        found = diff(old, new)
        ids = [item["obligation_id"] for item in found]
        actions = dict(connection.execute(OBLIGATION_TEXT, (ids,)).fetchall()) if ids else {}

    return ChangesResponse(
        from_run=from_run,
        to_run=to_run,
        changes=[
            Change(
                obligation_id=item["obligation_id"],
                before=item["before"],
                after=item["after"],
                direction=item["direction"],
                action=actions.get(item["obligation_id"], ""),
            )
            for item in found
        ],
    )


@app.get("/api/auth/tenants", response_model=list[Membership])
def my_tenants(user: SessionUser = Depends(require_user)) -> list[Membership]:
    with connect_app(user.tenant_id) as connection:
        rows = connection.execute(
            """
            SELECT t.id, t.name, m.role
            FROM membership m JOIN tenant t ON t.id = m.tenant_id
            WHERE m.user_id = %s
            ORDER BY t.name
            """,
            (user.id,),
        ).fetchall()
    return [Membership(tenant_id=row[0], name=row[1], role=row[2]) for row in rows]


@app.post("/api/auth/switch/{tenant_id}")
def switch_tenant(tenant_id: int, user: SessionUser = Depends(require_user)) -> dict:
    with connect_app(user.tenant_id) as connection:
        allowed = connection.execute(
            "SELECT 1 FROM membership WHERE user_id = %s AND tenant_id = %s",
            (user.id, tenant_id),
        ).fetchone()
        if allowed is None:
            raise HTTPException(status_code=403, detail="no access to tenant")
        connection.execute(
            "UPDATE app_user SET tenant_id = %s WHERE id = %s", (tenant_id, user.id)
        )
        connection.commit()
    return {"tenant_id": tenant_id}


@app.post("/api/tenants", response_model=Tenant, status_code=201)
def create_tenant(payload: NewTenant, user: SessionUser = Depends(require_owner)) -> Tenant:
    if AUTH_DISABLED and user.id == 0:
        raise HTTPException(status_code=503, detail="no local owner is seeded; run make demo")

    with connect_app(user.tenant_id) as connection:
        row = connection.execute(
            """
            INSERT INTO tenant (name, entity_type, products)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
            """,
            (payload.name.strip(), payload.entity_type, payload.products),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=409, detail="a workspace with that name exists")
        tenant_id = row[0]
        connection.execute(
            "INSERT INTO membership (user_id, tenant_id, role) VALUES (%s, %s, 'owner') "
            "ON CONFLICT DO NOTHING",
            (user.id, tenant_id),
        )
        connection.execute(
            "UPDATE app_user SET tenant_id = %s WHERE id = %s", (tenant_id, user.id)
        )
        connection.commit()

    return Tenant(
        id=tenant_id,
        name=payload.name.strip(),
        entity_type=payload.entity_type,
        license_type=None,
        products=payload.products,
        documents=0,
        clauses=0,
    )


@app.get("/api/tenants/{tenant_id}/documents/{document_id}/pdf")
def document_pdf(
    tenant_id: int,
    document_id: int,
    user: SessionUser = Depends(require_user),
):
    require_tenant(user, tenant_id)
    with connect_app(user.tenant_id) as connection:
        row = connection.execute(
            "SELECT sha256 FROM tenant_doc WHERE id = %s AND tenant_id = %s",
            (document_id, tenant_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="document not found")

    path = Path("data/tenant_pdfs") / f"{row[0]}.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="the original file is not stored")
    return FileResponse(path, media_type="application/pdf", filename=f"{document_id}.pdf")


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
            payload,
        )
        if document_id is None:
            raise HTTPException(status_code=409, detail="this document is already uploaded")
        embed_pending(connection, tenant_id)
        clause_count = connection.execute(
            "SELECT count(*) FROM tenant_clause WHERE tenant_doc_id = %s", (document_id,)
        ).fetchone()[0]

    return UploadResponse(document_id=document_id, title=title, clauses=clause_count, pages=pages)


@app.post("/api/tenants/{tenant_id}/map", response_model=MapJob, status_code=202)
def map_tenant(
    tenant_id: int,
    background: BackgroundTasks,
    limit: int = 10,
    user: SessionUser = Depends(require_owner),
) -> MapJob:
    require_tenant(user, tenant_id)
    bounded = max(1, min(limit, 50))

    with connect_app(user.tenant_id) as connection:
        job_id = start_job(connection, tenant_id, "map")

    background.add_task(run_map_job, job_id, tenant_id, bounded)
    return MapJob(job_id=job_id, status="queued")


@app.get("/api/tenants/{tenant_id}/jobs/{job_id}", response_model=JobStatus)
def job_status(
    tenant_id: int,
    job_id: int,
    user: SessionUser = Depends(require_user),
) -> JobStatus:
    require_tenant(user, tenant_id)
    with connect_app(user.tenant_id) as connection:
        row = connection.execute(
            "SELECT id, status, mapped, detail FROM job WHERE id = %s AND tenant_id = %s",
            (job_id, tenant_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatus(job_id=row[0], status=row[1], mapped=row[2], detail=row[3])


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
                policy_span=row[12],
                page=row[13],
                document_id=row[14],
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
        unsupported=answer.unsupported,
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
