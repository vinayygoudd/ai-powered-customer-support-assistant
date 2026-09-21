from flask import Blueprint, current_app, request
from app.api.auth import current_user
from app.services.auth_service import AuthError
from app.utils.validators import validate_message, ValidationError

tickets_bp = Blueprint("tickets", __name__)

@tickets_bp.post("/tickets")
def create_ticket():
    try:
        user = current_user()
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return {"error": "JSON object required"}, 400
        message = validate_message(payload.get("message"))
        ticket_id = current_app.extensions["services"]["tickets"].create_ticket(user["user_id"], message)
        return {"ticket_id": ticket_id, "status": "Open"}, 201
    except (ValidationError, AuthError) as exc:
        return {"error": str(exc)}, 400 if isinstance(exc, ValidationError) else 401
    except Exception:
        return {"error": "Unable to create ticket"}, 500

@tickets_bp.get("/tickets/<int:ticket_id>")
def get_ticket(ticket_id):
    try:
        user = current_user()
    except AuthError as exc:
        return {"error": str(exc)}, 401
    db = current_app.extensions["services"]["db"]
    ticket = db.get_ticket(ticket_id) if user["role"] == "admin" else db.get_ticket_for_user(ticket_id, user["user_id"])
    if not ticket:
        return {"error": "Ticket not found"}, 404
    ticket["human_review_required"] = bool(ticket["human_review_required"])
    ticket["predictions"] = db.get_predictions(ticket_id)
    ticket["ai_interactions"] = db.get_ai_interactions(ticket_id)
    ticket["feedback"] = db.get_feedback(ticket_id)
    return ticket, 200
