def test_review_queue_orders_priority(app):
    db = app.extensions["services"]["db"]
    u = db.get_or_create_user("review-user")
    a = db.create_ticket(u["user_id"], "critical")
    b = db.create_ticket(u["user_id"], "high")
    db.update_ticket_prediction(a, "Payment", "Critical", True)
    db.update_ticket_prediction(b, "Technical", "High", True)
    queue = db.review_queue()
    ids = [item["ticket_id"] for item in queue]
    assert ids[:2] == [a, b]

def test_analytics_shape(app):
    data = app.extensions["services"]["analytics"].summary()
    assert "total_tickets" in data
    assert "tickets_by_category" in data
    assert "tickets_by_priority" in data
