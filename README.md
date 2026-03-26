# UMT-pythonweb-hw-13

### Enviroment

Create `.env`

```dotenv
POSTGRES_DB=contacts_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

SECRET_KEY=123
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@example.com
MAIL_PORT=1025
MAIL_SERVER=mailpit
MAIL_FROM_NAME=Contacts API
MAIL_STARTTLS=False
MAIL_SSL_TLS=False
USE_CREDENTIALS=False
VALIDATE_CERTS=False

CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

CORS_ORIGINS=["*"]
```

## Cloudinary

Update `.env` to get working claudinary:

```env
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

### Run services

```bash
docker compose up --build
uvicorn src.main:app --reload
```

Services:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Mailpit UI: `http://localhost:8025`


## Tests

```bash
pytest -q
pytest --cov=src --cov-report=term-missing --cov-fail-under=75
```

## Docs Sphinx

```bash
sphinx-build -b html docs docs/_build
```

When get built, open `docs/_build/index.html`.

