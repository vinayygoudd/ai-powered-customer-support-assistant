from flask import Blueprint, current_app, request
from app.api.auth import current_user
from app.services.auth_service import AuthError
from app.utils.validators import validate_message, ValidationError

predictions_bp = Blueprint("predictions", __name__)

@predictions_bp.post("/predict")
def predict():
    try:
        user = current_user()
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get("ticket_id")) is not int:
            return {"error": "ticket_id must be an integer"}, 400
        db = current_app.extensions["services"]["db"]
        if user["role"] != "admin" and not db.get_ticket_for_user(payload["ticket_id"], user["user_id"]):
            return {"error": "Ticket not found"}, 404
        message = validate_message(payload["message"]) if "message" in payload else None
        result = current_app.extensions["services"]["tickets"].predict_ticket(payload["ticket_id"], message)
        return result, 200
    except AuthError as exc:
        return {"error": str(exc)}, 401
    except ValidationError as exc:
        return {"error": str(exc)}, 400
    except ValueError as exc:
        return {"error": str(exc)}, 404
    except FileNotFoundError as exc:
        return {"error": str(exc)}, 503
    except Exception:
        return {"error": "Prediction failed"}, 500
