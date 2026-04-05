import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Users


def _utcnow():
    return datetime.utcnow()


def create_access_token(user_id: int) -> str:
    payload = {
        "type": "access",
        "user_id": user_id,
        "exp": _utcnow() + timedelta(minutes = 30),
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "exp": _utcnow() + timedelta(days=14),
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        print(token)
        raise AuthenticationFailed("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")


class UsersJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.split(" ", 1)[1].strip()
        print(token)
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationFailed("Access token required")
        user_id = payload.get("user_id")
        user = Users.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationFailed("User not found")
        return (user, None)
