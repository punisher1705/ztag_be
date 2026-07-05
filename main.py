import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.core.config import get_settings

def main():
    try:
        settings = get_settings()
    except ValidationError as e:
        print("❌ Config validation FAILED — this is expected if .env is incomplete:\n")
        print(e)
        sys.exit(1)

    print("✅ Config loaded successfully.\n")
    print(f"App:              {settings.app_name} ({settings.app_env})")
    print(f"Database URL:     {settings.database_url}")
    print(f"Redis URL:        {settings.redis_url}")
    print(f"JWT algorithm:    {settings.jwt_algorithm}")
    print(f"Access token TTL: {settings.jwt_access_token_expires_minutes} min")
    print(f"Ollama model:     {settings.ollama_model} @ {settings.ollama_base_url}")
    print(f"Downstream svcs:  {settings.downstream_registry}")

if __name__ == "__main__":
    main()
