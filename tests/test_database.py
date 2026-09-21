def test_database_initialization_and_ticket_crud(app):
    db = app.extensions["services"]["db"]
    user = db.get_or_create_user("TEST-1")
    ticket_id = db.create_ticket(user["user_id"], "My app is crashing")
    ticket = db.get_ticket(ticket_id)
    assert ticket["message"] == "My app is crashing"
    assert ticket["status"] == "Open"
