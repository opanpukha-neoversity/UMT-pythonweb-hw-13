"""Shared pytest fixtures for unit and integration tests."""

from collections import deque
from pathlib import Path
import sys

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.db import Base, get_db
from src.database.models import User, UserRole
import src.main as main_module
from src.main import app
from src.services.auth import auth_service
from src.services import cache as cache_module
from src.api import users as users_api

SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


@pytest.fixture(scope='session', autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = Path('test.db')
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(cache_module, '_redis_client', fake)
    users_api._request_log.clear()
    yield


@pytest.fixture()
def session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(monkeypatch):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(main_module, 'engine', engine)
    monkeypatch.setattr('src.services.email.email_service.send_verification_email', lambda *args, **kwargs: None)
    monkeypatch.setattr('src.services.email.email_service.send_reset_email', lambda *args, **kwargs: None)
    monkeypatch.setattr('src.services.cloudinary_service.cloudinary_service.upload_avatar', lambda file, user_id: f'https://cdn.example.com/{user_id}.png')
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def user(session):
    user = User(
        username='tester',
        email='tester@example.com',
        hashed_password=auth_service.get_password_hash('secret123'),
        confirmed=True,
        role=UserRole.USER,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture()
def admin(session):
    user = User(
        username='admin',
        email='admin@example.com',
        hashed_password=auth_service.get_password_hash('secret123'),
        confirmed=True,
        role=UserRole.ADMIN,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture()
def token(user):
    return auth_service.create_access_token(user.email)


@pytest.fixture()
def admin_token(admin):
    return auth_service.create_access_token(admin.email)
