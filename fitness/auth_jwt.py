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
        "exp": _utcnow() + timedelta(minutes=30),
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
            algorithms=["HS256"],
            options={"verify_exp": False}  # временно отключаем проверку
        )
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")


class UsersJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):

        print("HEADERS:", request.headers)

        auth = request.headers.get("Authorization", "")
        print("AUTH HEADER:", auth)

        if not auth.startswith("Bearer "):
            print("NO BEARER")
            return None

        token = auth.split(" ", 1)[1].strip()
        print("TOKEN:", token)

        payload = decode_token(token)
        print("PAYLOAD:", payload)

        if payload.get("type") != "access":
            print("NOT ACCESS TOKEN")
            raise AuthenticationFailed("Access token required")

        user_id = payload.get("user_id")
        print("USER_ID:", user_id)

        user = Users.objects.filter(id=user_id).first()
        print("USER:", user)

        if not user:
            raise AuthenticationFailed("User not found")

        print("AUTH SUCCESS")

        return (user, None)
