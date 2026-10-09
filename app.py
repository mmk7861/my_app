import os
import secrets

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(32)),
        APP_NAME=os.getenv("APP_NAME", "Config Service"),
        DEMO_USERNAME=os.getenv("DEMO_USERNAME", "admin"),
        DEMO_PASSWORD=os.getenv("DEMO_PASSWORD", "welcome123"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        if session.get("username"):
            return redirect(url_for("welcome"))
        return render_template("login.html", app_name=app.config["APP_NAME"])

    @app.post("/login")
    def login():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        username_matches = secrets.compare_digest(
            username, app.config["DEMO_USERNAME"]
        )
        password_matches = secrets.compare_digest(
            password, app.config["DEMO_PASSWORD"]
        )

        if username_matches and password_matches:
            session.clear()
            session["username"] = username
            return redirect(url_for("welcome"))

        return (
            render_template(
                "login.html",
                app_name=app.config["APP_NAME"],
                error="The username or password is incorrect.",
                username=username,
            ),
            401,
        )

    @app.get("/welcome")
    def welcome():
        username = session.get("username")
        if not username:
            return redirect(url_for("index"))
        return render_template(
            "welcome.html",
            app_name=app.config["APP_NAME"],
            username=username,
        )

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    @app.get("/api/config")
    def public_config():
        return jsonify(
            appName=app.config["APP_NAME"],
            environment=os.getenv("APP_ENV", "development"),
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
