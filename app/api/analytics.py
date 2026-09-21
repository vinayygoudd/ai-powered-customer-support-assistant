from flask import Blueprint, current_app
from app.api.auth import current_user
from app.services.auth_service import AuthError

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.get("/analytics")
def analytics():
    try:
        user = current_user()
        if user["role"] != "admin":
            return {"error": "admin role required"}, 403
        return current_app.extensions["services"]["analytics"].summary(), 200
    except AuthError as exc:
        return {"error": str(exc)}, 401
