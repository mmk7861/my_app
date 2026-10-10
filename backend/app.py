import os
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from sqlalchemy import String, create_engine, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
password_hash = PasswordHash.recommended()


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


def create_app(test_config=None):
    config = {
        "SECRET_KEY": os.getenv("SECRET_KEY", secrets.token_hex(32)),
        "APP_NAME": os.getenv("APP_NAME", "Config Service"),
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "DATABASE_URL": os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://my_app_user@localhost:5432/my_app",
        ),
        "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME", "admin"),
        "ADMIN_PASSWORD": os.getenv("ADMIN_PASSWORD", "welcome123"),
    }
    if test_config:
        config.update(test_config)

    engine_options = {"pool_pre_ping": True}
    if config["DATABASE_URL"] == "sqlite:///:memory:":
        engine_options.update(
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    engine = create_engine(config["DATABASE_URL"], **engine_options)
    database_session = sessionmaker(bind=engine, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(engine)
        with database_session() as db_session:
            user = db_session.scalar(
                select(User).where(User.username == config["ADMIN_USERNAME"])
            )
            if user is None:
                user = User(
                    username=config["ADMIN_USERNAME"],
                    password_hash=password_hash.hash(config["ADMIN_PASSWORD"]),
                )
                db_session.add(user)
                db_session.commit()
            elif not user.password_hash.startswith("$argon2"):
                # One-time migration from the legacy password hash.
                user.password_hash = password_hash.hash(config["ADMIN_PASSWORD"])
                db_session.commit()

        yield
        engine.dispose()

    app = FastAPI(title=config["APP_NAME"], lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=config["SECRET_KEY"],
        same_site="lax",
        https_only=False,
    )
    app.mount(
        "/static",
        StaticFiles(directory=PROJECT_ROOT / "frontend" / "static"),
        name="static",
    )
    templates = Jinja2Templates(directory=PROJECT_ROOT / "frontend" / "templates")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if request.session.get("username"):
            return RedirectResponse(request.url_for("welcome"), status_code=303)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"app_name": config["APP_NAME"]},
        )

    @app.get("/register", response_class=HTMLResponse)
    def register_page(request: Request):
        if request.session.get("username"):
            return RedirectResponse(request.url_for("welcome"), status_code=303)
        return templates.TemplateResponse(
            request,
            "register.html",
            {"app_name": config["APP_NAME"]},
        )

    @app.post("/register", response_class=HTMLResponse)
    def register(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        confirm_password: Annotated[str, Form()],
    ):
        username = username.strip()
        error = None

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", username):
            error = (
                "Username must be 3–32 characters and use only letters, "
                "numbers, dots, underscores, or hyphens."
            )
        elif len(password) < 8:
            error = "Password must contain at least 8 characters."
        elif password != confirm_password:
            error = "The passwords do not match."

        if error:
            return templates.TemplateResponse(
                request,
                "register.html",
                {
                    "app_name": config["APP_NAME"],
                    "error": error,
                    "username": username,
                },
                status_code=400,
            )

        with database_session() as db_session:
            existing_user = db_session.scalar(
                select(User).where(User.username == username)
            )
            if existing_user:
                return templates.TemplateResponse(
                    request,
                    "register.html",
                    {
                        "app_name": config["APP_NAME"],
                        "error": "That username is already registered.",
                        "username": username,
                    },
                    status_code=409,
                )

            user = User(
                username=username,
                password_hash=password_hash.hash(password),
            )
            db_session.add(user)
            try:
                db_session.commit()
            except IntegrityError:
                db_session.rollback()
                return templates.TemplateResponse(
                    request,
                    "register.html",
                    {
                        "app_name": config["APP_NAME"],
                        "error": "That username is already registered.",
                        "username": username,
                    },
                    status_code=409,
                )

        request.session.clear()
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        return RedirectResponse(request.url_for("welcome"), status_code=303)

    @app.post("/login", response_class=HTMLResponse)
    def login(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ):
        username = username.strip()
        with database_session() as db_session:
            user = db_session.scalar(select(User).where(User.username == username))

        credentials_valid = bool(
            user
            and user.password_hash.startswith("$argon2")
            and password_hash.verify(password, user.password_hash)
        )
        if credentials_valid:
            request.session.clear()
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            return RedirectResponse(request.url_for("welcome"), status_code=303)

        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "app_name": config["APP_NAME"],
                "error": "The username or password is incorrect.",
                "username": username,
            },
            status_code=401,
        )

    @app.get("/welcome", response_class=HTMLResponse)
    def welcome(request: Request):
        username = request.session.get("username")
        if not username:
            return RedirectResponse(request.url_for("index"), status_code=303)
        return templates.TemplateResponse(
            request,
            "welcome.html",
            {"app_name": config["APP_NAME"], "username": username},
        )

    @app.post("/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse(request.url_for("index"), status_code=303)

    @app.get("/api/config")
    def public_config():
        return {
            "appName": config["APP_NAME"],
            "environment": config["APP_ENV"],
        }

    @app.get("/health")
    def health():
        try:
            with database_session() as db_session:
                db_session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse(
                {"status": "error", "database": "unavailable"},
                status_code=503,
            )
        return {"status": "ok", "database": "connected"}

    return app


app = create_app()
