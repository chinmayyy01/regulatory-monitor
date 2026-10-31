import os
import time
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from app.auth.passwords import verify_password
from app.auth.sessions import create_session, delete_session, user_for_token
from app.chat.answer import ask as answer_question
from app.chat.retrieve import gather
from app.db import apply_schema, connect, connect_app

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
_attempts: dict[str, tuple[int, float]] = {}


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


def require_tenant(user: SessionUser, tenant_id: int) -> None:
    if user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your tenant")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: Credentials) -> LoginResponse:
    email = credentials.email.lower().strip()
    attempts, locked_until = _attempts.get(email, (0, 0.0))
    if locked_until > time.time():
        raise HTTPException(status_code=429, detail="too many attempts, try again later")

    with connect_app() as connection:
        row = connection.execute(USER_LOGIN, (email,)).fetchone()
        if row is None or not verify_password(credentials.password, row[2]):
            _attempts[email] = (attempts + 1, time.time() + LOCKOUT_SECONDS if attempts + 1 >= MAX_ATTEMPTS else 0.0)
            raise HTTPException(status_code=401, detail="invalid email or password")
        token = create_session(connection, row[0])

    _attempts.pop(email, None)
    return LoginResponse(
        token=token,
        user=SessionUser(id=row[0], email=row[1], tenant_id=row[3], role=row[4]),
    )


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    token = token_from_header(authorization)
    if token:
        with connect_app() as connection:
            delete_session(connection, token)
    return {"status": "signed out"}


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
