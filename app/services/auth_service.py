import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

class AuthError(ValueError):
    pass

class AuthService:
    def __init__(self, db, secret_key, token_ttl_seconds=3600):
        self.db = db
        self.serializer = URLSafeTimedSerializer(secret_key, salt="support-assistant-auth")
        self.token_ttl_seconds = token_ttl_seconds

    @staticmethod
    def hash_password(password):
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32
        )
        return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password, encoded):
        try:
            _, n, r, p, salt_hex, digest_hex = encoded.split("$")
            candidate = hashlib.scrypt(
                password.encode("utf-8"),
                salt=bytes.fromhex(salt_hex),
                n=int(n), r=int(r), p=int(p), dklen=32
            )
            return hmac.compare_digest(candidate.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    def register(self, name, email, password, role="customer"):
        if len(password) < 10:
            raise AuthError("password must be at least 10 characters")
        if role not in {"customer", "admin"}:
            raise AuthError("invalid role")
        return self.db.create_user(name, email.lower().strip(), self.hash_password(password), role)

    def login(self, email, password):
        user = self.db.get_user_by_email(email.lower().strip())
        if not user or not self.verify_password(password, user["password_hash"]):
            raise AuthError("invalid credentials")
        token = self.serializer.dumps({"user_id": user["user_id"], "role": user["role"]})
        return token, user

    def verify_token(self, token):
        try:
            data = self.serializer.loads(token, max_age=self.token_ttl_seconds)
        except (BadSignature, SignatureExpired) as exc:
            raise AuthError("invalid or expired token") from exc
        user = self.db.get_user(data["user_id"])
        if not user:
            raise AuthError("user not found")
        return user

def bearer_token(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise AuthError("Authorization: Bearer <token> is required")
    token = header[7:].strip()
    if not token:
        raise AuthError("bearer token is empty")
    return token
