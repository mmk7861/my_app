# Config Service starter

A small full-stack starter with a FastAPI backend, PostgreSQL-backed login,
session authentication, a protected welcome page, and public config/health APIs.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Replace `your-password` in .env with the password for my_app_user.
set -a; source .env; set +a
uvicorn backend.app:app --port 8000 --reload
```

Open <http://localhost:8000> and sign in using `admin` / `welcome123`, or use
the credentials configured with `ADMIN_USERNAME` and `ADMIN_PASSWORD`. Database
tables and the initial user are created automatically when the service starts.
New users can create their own account at <http://localhost:8000/register>.

## Share on the local Wi-Fi

If the macOS application firewall blocks pyenv Python even after it is allowed,
keep FastAPI running on port 8000 and run this in a second terminal:

```bash
ruby scripts/lan_proxy.rb
```

Other devices on the same trusted Wi-Fi can then open
`http://YOUR-MAC-IP:8080`. This proxy uses the macOS-provided Ruby executable;
it is intended only for local development.

## PostgreSQL

The default local connection is:

```text
Host: localhost
Port: 5432
Database: my_app
Username: my_app_user
```

Set `DATABASE_URL` in `.env` when a password is required. The `/health`
endpoint returns HTTP 503 if the database cannot be reached.

For any deployed environment, set a long random `SECRET_KEY`, replace the demo
credentials, enable HTTPS, and use an identity provider or database-backed user
store instead of environment variables.
