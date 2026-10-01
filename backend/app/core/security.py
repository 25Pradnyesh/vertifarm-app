import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _b64url_decode(data_str: str) -> bytes:
    padded = data_str + '=' * (-len(data_str) % 4)
    return base64.urlsafe_b64decode(padded)

def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """
    Creates a signed HS256 JWT access token.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    
    now = int(time.time())
    if expires_delta_seconds:
        payload["exp"] = now + expires_delta_seconds
    else:
        payload["exp"] = now + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    payload["iat"] = now

    header_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
    signature = hmac.new(settings.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validates signature and expiration of an HS256 JWT access token.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        expected_sig = _b64url_encode(hmac.new(settings.JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest())

        if not hmac.compare_digest(sig_b64, expected_sig):
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Check expiration
        exp = payload.get("exp")
        if exp and int(time.time()) > exp:
            return None

        return payload
    except Exception:
        return None

def decode_unverified_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes the payload of a JWT without signature verification (for inspect/dev fallback).
    """
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return None
        payload_bytes = _b64url_decode(parts[1])
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return None

def verify_google_id_token(token_str: str) -> Dict[str, Any]:
    """
    Verifies a Google OAuth 2.0 ID token.
    In production: Validates cryptographic signature against Google's public certs.
    In development: If ALLOW_DEV_AUTH is true and offline, falls back to dev validation.
    """
    client_ids = [
        cid for cid in [
            settings.GOOGLE_CLIENT_ID,
            settings.GOOGLE_WEB_CLIENT_ID,
            settings.GOOGLE_IOS_CLIENT_ID,
            settings.GOOGLE_ANDROID_CLIENT_ID,
        ] if cid and not cid.startswith("vertifarm-placeholder")
    ]

    # 1. Attempt verification with client IDs if configured
    if client_ids:
        request = google_requests.Request()
        for cid in client_ids:
            try:
                id_info = google_id_token.verify_oauth2_token(token_str, request, cid)
                return {
                    "id": id_info.get("sub"),
                    "google_id": id_info.get("sub"),
                    "email": id_info.get("email"),
                    "name": id_info.get("name") or (id_info.get("email", "").split("@")[0] if id_info.get("email") else "Grower"),
                    "picture": id_info.get("picture"),
                }
            except Exception:
                continue

    # 2. Attempt generic verification with Google certs (no audience filter)
    try:
        request = google_requests.Request()
        id_info = google_id_token.verify_oauth2_token(token_str, request)
        return {
            "id": id_info.get("sub"),
            "google_id": id_info.get("sub"),
            "email": id_info.get("email"),
            "name": id_info.get("name") or (id_info.get("email", "").split("@")[0] if id_info.get("email") else "Grower"),
            "picture": id_info.get("picture"),
        }
    except Exception as e:
        # 3. Development-only fallback if explicitly allowed
        if settings.ALLOW_DEV_AUTH:
            dev_claims = decode_unverified_jwt(token_str)
            if dev_claims and "sub" in dev_claims and "email" in dev_claims:
                return {
                    "id": dev_claims.get("sub"),
                    "google_id": dev_claims.get("sub"),
                    "email": dev_claims.get("email"),
                    "name": dev_claims.get("name") or dev_claims.get("email", "").split("@")[0],
                    "picture": dev_claims.get("picture"),
                }
            if token_str.startswith("dev-token-") or token_str == "test-google-token":
                user_id = token_str.replace("dev-token-", "") if token_str.startswith("dev-token-") else "usr-google-test"
                return {
                    "id": user_id,
                    "google_id": user_id,
                    "email": f"{user_id}@vertifarm.io",
                    "name": "Dev Grower",
                    "picture": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200",
                }
        raise ValueError(f"Invalid Google ID token: {str(e)}")
