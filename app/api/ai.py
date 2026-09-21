from flask import Blueprint, current_app, request
from app.api.auth import current_user
from app.services.auth_service import AuthError
from app.utils.validators import validate_rating, validate_message, ValidationError

ai_bp = Blueprint("ai", __name__)

def _authorized_ticket(ticket_id, user):
    db = current_app.extensions["services"]["db"]
    return db.get_ticket(ticket_id) if user["role"] == "admin" else db.get_ticket_for_user(ticket_id, user["user_id"])

@ai_bp.post("/generate-response")
def generate_response():
    try:
        user = current_user()
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get("ticket_id")) is not int:
            return {"error": "ticket_id must be an integer"}, 400
        if not _authorized_ticket(payload["ticket_id"], user):
            return {"error": "Ticket not found"}, 404
        return current_app.extensions["services"]["tickets"].generate_response(payload["ticket_id"]), 200
    except AuthError as exc:
        return {"error": str(exc)}, 401
    except ValueError as exc:
        return {"error": str(exc)}, 404
    except Exception:
        return {"error": "AI response generation failed"}, 500

@ai_bp.post("/process-ticket")
def process_ticket():
    try:
        user = current_user()
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return {"error": "JSON object required"}, 400
        message = validate_message(payload.get("message"))
        result = current_app.extensions["services"]["tickets"].process_ticket_atomic(user["user_id"], message)
        return result, 201
    except AuthError as exc:
        return {"error": str(exc)}, 401
    except ValidationError as exc:
        return {"error": str(exc)}, 400
    except FileNotFoundError as exc:
        return {"error": str(exc)}, 503
    except Exception:
        return {"error": "Ticket processing failed"}, 500

@ai_bp.post("/feedback")
def feedback():
    try:
        user = current_user()
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get("ticket_id")) is not int:
            return {"error": "ticket_id must be an integer"}, 400
        ticket = _authorized_ticket(payload["ticket_id"], user)
        if not ticket:
            return {"error": "Ticket not found"}, 404
        rating = validate_rating(payload.get("rating"))
        comments = payload.get("comments", "")
        if type(comments) is not str:
            return {"error": "comments must be a string"}, 400
        current_app.extensions["services"]["db"].add_feedback(payload["ticket_id"], rating, comments.strip()[:2000])
        return {"status": "stored"}, 201
    except AuthError as exc:
        return {"error": str(exc)}, 401
    except ValidationError as exc:
        return {"error": str(exc)}, 400

@ai_bp.get("/review-queue")
def review_queue():
    try:
        user = current_user()
        if user["role"] != "admin":
            return {"error": "admin role required"}, 403
        return {"tickets": current_app.extensions["services"]["db"].review_queue()}, 200
    except AuthError as exc:
        return {"error": str(exc)}, 401
