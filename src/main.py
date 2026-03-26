"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.api.contacts import router as contacts_router
from src.api.users import router as users_router
from src.conf.config import get_settings
from src.database.db import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the application starts."""

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title='Contacts API',
    version='3.0.0',
    description='Contacts REST API with auth, Redis cache and tests',
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(users_router)


@app.get('/', tags=['healthcheck'])
def healthcheck():
    """Return a small health-check payload."""

    return {'message': 'Contacts API is running'}
