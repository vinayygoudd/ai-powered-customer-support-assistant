from app.utils.config import Settings
from app.services.database_service import DatabaseManager

if __name__ == "__main__":
    settings = Settings.from_env()
    DatabaseManager(settings.database_path).initialize()
    print(f"Database initialized at {settings.database_path}")
