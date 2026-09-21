import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.redis_client import get_redis
from app.db.session import SessionLocal
from app.main import app
from app.models.user import Role
from app.services import auth_service
from app.services.embedding_service import get_embedding_service
from app.services.retrieval_service import RetrievalService

_RESET_TABLES = "audit_log, refresh_tokens, password_reset_tokens, messages, conversations, users"


@pytest.fixture(scope="session")
def client():
    # Runs the FastAPI lifespan once for the whole test session, so the
    # embedding and Whisper models load only once, not per test. Per-route
    # rate limits (e.g. 5/minute on /auth/login) are real security controls
    # exercised by test_security_headers/test_auth directly; disabling them
    # here just stops the rest of the suite, which logs in many different
    # test users, from tripping over that same limit.
    app.state.limiter.enabled = False
    with TestClient(app) as test_client:
        yield test_client
    app.state.limiter.enabled = True


@pytest.fixture(autouse=True)
def _reset_state():
    db = SessionLocal()
    # A stuck or leaked connection from an earlier test holding any lock on
    # these tables would otherwise make TRUNCATE hang indefinitely with no
    # useful error. Fail fast instead.
    db.execute(text("SET lock_timeout = '5s'"))
    db.execute(text(f"TRUNCATE {_RESET_TABLES} RESTART IDENTITY CASCADE"))
    db.commit()
    db.close()
    get_redis().flushdb()
    yield


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def make_user(db_session):
    """Signs up a real user, promotes them to the given role, and returns the User."""

    def _make(email: str, password: str = "verifypassword123", role: str = "agent", full_name: str = "Test User"):
        user = auth_service.signup(db_session, email=email, password=password, full_name=full_name)
        role_row = db_session.query(Role).filter(Role.name == role).first()
        user.role_id = role_row.id
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def auth_headers(client, make_user):
    """Returns a function(email, role) -> Authorization header dict for a freshly logged-in user."""

    def _make(email: str, role: str = "agent", password: str = "verifypassword123"):
        make_user(email, password=password, role=role)
        response = client.post("/auth/login", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make


@pytest.fixture
def kb_query(db_session):
    """A real support_kb instruction, guaranteed to score above the KB-direct
    threshold when asked verbatim, so tests don't depend on live LLM keys.
    """
    retrieval = RetrievalService(db_session, get_embedding_service())
    return retrieval.search("order refund", top_k=1)[0].instruction
