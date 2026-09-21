def register_and_login(client, email="user@example.com"):
    assert client.post("/api/auth/register", json={
        "name": "User", "email": email, "password": "long-secure-password"
    }).status_code == 201
    response = client.post("/api/auth/login", json={
        "email": email, "password": "long-secure-password"
    })
    assert response.status_code == 200
    return response.json["access_token"]

def test_create_ticket_requires_auth(client):
    response = client.post("/api/tickets", json={"message": "I need help"})
    assert response.status_code == 401

def test_create_and_get_ticket(client):
    token = register_and_login(client)
    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "I cannot sign in."},
    )
    assert response.status_code == 201
    ticket_id = response.json["ticket_id"]
    response = client.get(
        f"/api/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json["ticket_id"] == ticket_id

def test_process_endpoint_requires_auth(client):
    response = client.post("/api/process-ticket", json={"message": "My payment failed"})
    assert response.status_code == 401
