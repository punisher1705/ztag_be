"""Entrypoint used by gunicorn in production/staging. `gunicorn app.wsgi:app`"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Only used for `python -m app.wsgi` local debugging without gunicorn.
    settings_app = app
    app.run(host="0.0.0.0", port=5001, debug=app.config.get("DEBUG", False))