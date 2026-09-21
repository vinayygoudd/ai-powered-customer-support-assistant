from dataclasses import dataclass

@dataclass
class User:
    user_id: int | None
    name: str
    email: str
    created_at: str | None = None
