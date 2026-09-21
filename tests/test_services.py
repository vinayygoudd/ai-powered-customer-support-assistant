from app.services.priority_queue import PriorityQueueManager

def test_priority_queue_orders_by_priority():
    q = PriorityQueueManager()
    q.add(1, "Low")
    q.add(2, "Critical")
    q.add(3, "High")
    assert q.pop_next() == 2
    assert q.pop_next() == 3
    assert q.pop_next() == 1

def test_mock_llm(app):
    llm = app.extensions["services"]["llm"]
    response = llm.generate("Customer message: I need help\nPredicted category: Billing")
    assert response
    assert llm.validate_response(response)
