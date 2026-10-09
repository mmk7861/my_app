# Config Service starter

A small full-stack starter with a Flask backend, server-rendered login UI,
session authentication, a protected welcome page, and public config/health APIs.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
flask --app app run --port 8000 --debug
```

Open <http://localhost:8000> and sign in using `admin` / `welcome123`, or use
the credentials configured in `.env`.

## Run with Docker

```bash
docker build -t config-service .
docker run --rm -p 8000:8000 --env-file .env config-service
```

For any deployed environment, set a long random `SECRET_KEY`, replace the demo
credentials, enable HTTPS, and use an identity provider or database-backed user
store instead of environment variables.
