def test_register_login_and_authorization(client):
    register = client.post("/api/auth/register", json={
        "name": "Alice", "email": "alice@example.com", "password": "long-secure-password"
    })
    assert register.status_code == 201
    login = client.post("/api/auth/login", json={
        "email": "alice@example.com", "password": "long-secure-password"
    })
    assert login.status_code == 200
    token = login.json["access_token"]
    created = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "My invoice is incorrect."},
    )
    assert created.status_code == 201
    fetched = client.get(
        f"/api/tickets/{created.json['ticket_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200

def test_customer_cannot_read_other_customer_ticket(client):
    for name, email in [("A", "a@example.com"), ("B", "b@example.com")]:
        assert client.post("/api/auth/register", json={
            "name": name, "email": email, "password": "long-secure-password"
        }).status_code == 201
    a = client.post("/api/auth/login", json={"email":"a@example.com","password":"long-secure-password"}).json["access_token"]
    b = client.post("/api/auth/login", json={"email":"b@example.com","password":"long-secure-password"}).json["access_token"]
    ticket = client.post("/api/tickets", headers={"Authorization":f"Bearer {a}"}, json={"message":"Private issue"}).json["ticket_id"]
    assert client.get(f"/api/tickets/{ticket}", headers={"Authorization":f"Bearer {b}"}).status_code == 404
