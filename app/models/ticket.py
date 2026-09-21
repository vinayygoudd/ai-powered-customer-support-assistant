from dataclasses import dataclass

@dataclass
class Ticket:
    ticket_id: int | None
    user_id: int
    message: str
    category: str | None = None
    priority: str | None = None
    status: str = "Open"
    created_at: str | None = None
    human_review_required: bool = False
