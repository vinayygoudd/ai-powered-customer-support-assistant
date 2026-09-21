import sqlite3
from pathlib import Path
from contextlib import contextmanager


class DatabaseManager:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        """Create a configured SQLite connection."""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self):
        """Open a standalone database connection and commit/rollback automatically."""
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Open one connection for a multi-step atomic transaction."""
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'customer'
                        CHECK(role IN ('customer', 'admin')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    status TEXT NOT NULL DEFAULT 'Open',
                    human_review_required INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    predicted_category TEXT NOT NULL,
                    predicted_priority TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id)
                        REFERENCES tickets(ticket_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS ai_interactions (
                    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    prompt_version TEXT NOT NULL,
                    generated_response TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id)
                        REFERENCES tickets(ticket_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                    comments TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id)
                        REFERENCES tickets(ticket_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tickets_user
                    ON tickets(user_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_status
                    ON tickets(status);
                CREATE INDEX IF NOT EXISTS idx_tickets_priority
                    ON tickets(priority);
                CREATE INDEX IF NOT EXISTS idx_predictions_ticket
                    ON predictions(ticket_id);
                CREATE INDEX IF NOT EXISTS idx_ai_ticket
                    ON ai_interactions(ticket_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_ticket
                    ON feedback(ticket_id);
                """
            )

            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(users)").fetchall()
            }

            if "password_hash" not in columns:
                conn.execute(
                    "ALTER TABLE users "
                    "ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''"
                )

            if "role" not in columns:
                conn.execute(
                    "ALTER TABLE users "
                    "ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'"
                )

            ticket_columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(tickets)").fetchall()
            }

            if "human_review_required" not in ticket_columns:
                conn.execute(
                    "ALTER TABLE tickets "
                    "ADD COLUMN human_review_required INTEGER NOT NULL DEFAULT 0"
                )

    def create_user(self, name, email, password_hash, role="customer"):
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO users(name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password_hash, role),
            )
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (cur.lastrowid,),
            ).fetchone()
            return dict(row)

    def get_user_by_email(self, email):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,),
            ).fetchone()
            return dict(row) if row else None

    def get_user(self, user_id):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_or_create_user(self, customer_id):
        """Backward-compatible helper for seeded/internal usage."""
        email = f"{customer_id}@customer.local"
        user = self.get_user_by_email(email)

        if user:
            return user

        password_hash = "legacy"
        return self.create_user(
            customer_id,
            email,
            password_hash,
            "customer",
        )

    def create_ticket(self, user_id, message, conn=None):
        """
        Create a ticket.

        If conn is supplied, the insert participates in the caller's
        transaction. Otherwise, this method manages its own connection.
        """
        target = conn if conn is not None else self._connect()
        close = conn is None

        try:
            cur = target.execute(
                """
                INSERT INTO tickets(user_id, message)
                VALUES (?, ?)
                """,
                (user_id, message),
            )

            if close:
                target.commit()

            return cur.lastrowid
        finally:
            if close:
                target.close()

    def get_ticket(self, ticket_id, conn=None):
        """
        Fetch a ticket.

        If conn is supplied, the query uses that same connection. This is
        important when the ticket was created inside an uncommitted
        transaction and must immediately be read by another operation in
        that same transaction.
        """
        target = conn if conn is not None else self._connect()
        close = conn is None

        try:
            row = target.execute(
                """
                SELECT
                    t.*,
                    u.name AS customer_name,
                    u.email AS customer_email
                FROM tickets t
                JOIN users u ON u.user_id = t.user_id
                WHERE t.ticket_id = ?
                """,
                (ticket_id,),
            ).fetchone()

            return dict(row) if row else None
        finally:
            if close:
                target.close()

    def get_ticket_for_user(self, ticket_id, user_id):
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT
                    t.*,
                    u.name AS customer_name,
                    u.email AS customer_email
                FROM tickets t
                JOIN users u ON u.user_id = t.user_id
                WHERE t.ticket_id = ? AND t.user_id = ?
                """,
                (ticket_id, user_id),
            ).fetchone()

            return dict(row) if row else None

    def update_ticket_prediction(
        self,
        ticket_id,
        category,
        priority,
        human_review_required,
        conn=None,
    ):
        """
        Update prediction fields.

        If conn is supplied, the update remains inside the caller's
        transaction.
        """
        target = conn if conn is not None else self._connect()
        close = conn is None

        try:
            target.execute(
                """
                UPDATE tickets
                SET category = ?,
                    priority = ?,
                    human_review_required = ?
                WHERE ticket_id = ?
                """,
                (
                    category,
                    priority,
                    int(human_review_required),
                    ticket_id,
                ),
            )

            if close:
                target.commit()
        finally:
            if close:
                target.close()

    def set_human_review(self, ticket_id, required=True):
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET human_review_required = ?
                WHERE ticket_id = ?
                """,
                (int(required), ticket_id),
            )

    def update_status(self, ticket_id, status):
        with self.connection() as conn:
            conn.execute(
                "UPDATE tickets SET status = ? WHERE ticket_id = ?",
                (status, ticket_id),
            )

    def add_prediction(
        self,
        ticket_id,
        category,
        priority,
        model_version,
        conn=None,
    ):
        """Persist a prediction using the caller's transaction when supplied."""
        target = conn if conn is not None else self._connect()
        close = conn is None

        try:
            target.execute(
                """
                INSERT INTO predictions(
                    ticket_id,
                    predicted_category,
                    predicted_priority,
                    model_version
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    category,
                    priority,
                    model_version,
                ),
            )

            if close:
                target.commit()
        finally:
            if close:
                target.close()

    def add_ai_interaction(
        self,
        ticket_id,
        prompt_version,
        response,
        conn=None,
    ):
        """Persist an AI interaction using the caller's transaction."""
        target = conn if conn is not None else self._connect()
        close = conn is None

        try:
            target.execute(
                """
                INSERT INTO ai_interactions(
                    ticket_id,
                    prompt_version,
                    generated_response
                )
                VALUES (?, ?, ?)
                """,
                (
                    ticket_id,
                    prompt_version,
                    response,
                ),
            )

            if close:
                target.commit()
        finally:
            if close:
                target.close()

    def add_feedback(self, ticket_id, rating, comments):
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback(ticket_id, rating, comments)
                VALUES (?, ?, ?)
                """,
                (ticket_id, rating, comments),
            )

    def get_predictions(self, ticket_id):
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM predictions
                WHERE ticket_id = ?
                ORDER BY prediction_id DESC
                """,
                (ticket_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_ai_interactions(self, ticket_id):
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM ai_interactions
                WHERE ticket_id = ?
                ORDER BY interaction_id DESC
                """,
                (ticket_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_feedback(self, ticket_id):
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM feedback
                WHERE ticket_id = ?
                ORDER BY feedback_id DESC
                """,
                (ticket_id,),
            ).fetchall()

            return [dict(row) for row in rows]

    def review_queue(self):
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.ticket_id,
                    t.message,
                    t.category,
                    t.priority,
                    t.status,
                    t.human_review_required,
                    t.created_at,
                    u.name AS customer_name
                FROM tickets t
                JOIN users u ON u.user_id = t.user_id
                WHERE t.human_review_required = 1
                  AND t.status != 'Resolved'
                ORDER BY
                    CASE t.priority
                        WHEN 'Critical' THEN 0
                        WHEN 'High' THEN 1
                        WHEN 'Medium' THEN 2
                        ELSE 3
                    END,
                    t.created_at ASC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def analytics(self):
        with self.connection() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM tickets"
            ).fetchone()[0]

            open_count = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE status = 'Open'"
            ).fetchone()[0]

            resolved = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'"
            ).fetchone()[0]

            critical = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE priority = 'Critical'"
            ).fetchone()[0]

            ai_count = conn.execute(
                "SELECT COUNT(*) FROM ai_interactions"
            ).fetchone()[0]

            avg_rating = conn.execute(
                "SELECT AVG(rating) FROM feedback"
            ).fetchone()[0]

            by_category = {
                row["category"]: row["count"]
                for row in conn.execute(
                    """
                    SELECT
                        COALESCE(category, 'Unknown') AS category,
                        COUNT(*) AS count
                    FROM tickets
                    GROUP BY category
                    """
                )
            }

            by_priority = {
                row["priority"]: row["count"]
                for row in conn.execute(
                    """
                    SELECT
                        COALESCE(priority, 'Unknown') AS priority,
                        COUNT(*) AS count
                    FROM tickets
                    GROUP BY priority
                    """
                )
            }

            avg_resolution = conn.execute(
                """
                SELECT AVG(
                    (julianday('now') - julianday(created_at)) * 24
                )
                FROM tickets
                WHERE status = 'Resolved'
                """
            ).fetchone()[0]

            return {
                "total_tickets": total,
                "open_tickets": open_count,
                "resolved_tickets": resolved,
                "critical_tickets": critical,
                "ai_interaction_count": ai_count,
                "average_feedback_rating": (
                    round(avg_rating, 2)
                    if avg_rating is not None
                    else None
                ),
                "average_resolution_time_hours": (
                    round(avg_resolution, 2)
                    if avg_resolution is not None
                    else None
                ),
                "tickets_by_category": by_category,
                "tickets_by_priority": by_priority,
            }
