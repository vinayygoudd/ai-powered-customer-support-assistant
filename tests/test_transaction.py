def test_transaction_rolls_back_on_exception(app):
    db = app.extensions["services"]["db"]
    user = db.get_or_create_user("transaction-user")
    try:
        with db.transaction() as conn:
            db.create_ticket(user["user_id"], "must rollback", conn=conn)
            raise RuntimeError("force rollback")
    except RuntimeError:
        pass
    with db.connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE message=?", ("must rollback",)
        ).fetchone()[0]
    assert count == 0
