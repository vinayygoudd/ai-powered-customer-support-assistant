import getpass
from app.utils.config import Settings
from app.services.database_service import DatabaseManager
from app.services.auth_service import AuthService

if __name__ == "__main__":
    settings = Settings.from_env()
    db = DatabaseManager(settings.database_path)
    db.initialize()
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password (10+ chars): ")
    user = AuthService(db, settings.secret_key).register(name, email, password, role="admin")
    print(f"Created admin user {user['user_id']} ({user['email']}).")
