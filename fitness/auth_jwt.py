# app/auth_jwt.py
import jwt
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Users


ACCESS_MINUTES = 30
REFRESH_DAYS = 7


def _now():
    return datetime.now(timezone.utc)


def make_access_token(user: Users) -> str:
    payload = {
        "type": "access",
        "user_id": user.id,
        "email": user.email,
        "exp": _now() + timedelta(minutes=ACCESS_MINUTES),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def make_refresh_token(user: Users) -> str:
    payload = {
        "type": "refresh",
        "user_id": user.id,
        "email": user.email,
        "exp": _now() + timedelta(days=REFRESH_DAYS),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")


@dataclass
class SimpleUser:
    id: int
    email: str
    is_authenticated: bool = True


class UsersJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None

        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationFailed("Invalid token type")

        user_id = payload.get("user_id")
        email = payload.get("email")
        if not user_id:
            raise AuthenticationFailed("Invalid token payload")

        # опционально проверим, что пользователь существует
        if not Users.objects.filter(id=user_id).exists():
            raise AuthenticationFailed("User not found")

        return (SimpleUser(id=user_id, email=email), None)
