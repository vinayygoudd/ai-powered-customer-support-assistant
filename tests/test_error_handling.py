def test_json_and_type_validation(client):
    assert client.post("/api/tickets", data="not-json", content_type="text/plain").status_code == 401
    reg = client.post("/api/auth/register", json={
        "name":"A","email":"a@example.com","password":"long-secure-password"
    })
    assert reg.status_code == 201
    token = client.post("/api/auth/login", json={
        "email":"a@example.com","password":"long-secure-password"
    }).json["access_token"]
    response = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": 123},
    )
    assert response.status_code == 400
