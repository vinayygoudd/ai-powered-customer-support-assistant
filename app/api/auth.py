from flask import Blueprint, current_app, request
from app.services.auth_service import AuthError, bearer_token
from app.utils.validators import ValidationError

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/auth/register")
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "JSON object required"}, 400
    try:
        name = payload.get("name")
        email = payload.get("email")
        password = payload.get("password")
        if not all(isinstance(x, str) for x in (name, email, password)):
            raise ValidationError("name, email, and password must be strings")
        user = current_app.extensions["services"]["auth"].register(name.strip(), email.strip(), password)
        user.pop("password_hash", None)
        return user, 201
    except ValidationError as exc:
        return {"error": str(exc)}, 400
    except AuthError as exc:
        return {"error": str(exc)}, 400
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return {"error": "email already registered"}, 409
        return {"error": "registration failed"}, 500

@auth_bp.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"error": "JSON object required"}, 400
    email, password = payload.get("email"), payload.get("password")
    if type(email) is not str or type(password) is not str:
        return {"error": "email and password must be strings"}, 400
    try:
        token, user = current_app.extensions["services"]["auth"].login(email, password)
        return {"access_token": token, "user_id": user["user_id"], "role": user["role"]}, 200
    except AuthError as exc:
        return {"error": str(exc)}, 401

def current_user():
    token = bearer_token(request)
    return current_app.extensions["services"]["auth"].verify_token(token)
