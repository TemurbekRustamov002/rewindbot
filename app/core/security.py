import base64
import hashlib
import hmac
import secrets
from typing import Optional
from app.core.config import settings


def _get_derived_key() -> bytes:
    raw_key = settings.ENCRYPTION_KEY.encode()
    return hashlib.sha256(raw_key).digest()


def encrypt_data(text: str) -> str:
    """
    Encrypts text using standard library HMAC/Stream cipher (cross-platform, zero C-deps).
    """
    if not text:
        return text
    key = _get_derived_key()
    nonce = secrets.token_bytes(16)
    keystream = hashlib.sha256(key + nonce).digest()
    
    text_bytes = text.encode("utf-8")
    # Keystream expansion if text is longer
    expanded_keystream = b""
    counter = 0
    while len(expanded_keystream) < len(text_bytes):
        expanded_keystream += hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
        counter += 1

    encrypted_bytes = bytes([b ^ k for b, k in zip(text_bytes, expanded_keystream)])
    mac = hmac.new(key, nonce + encrypted_bytes, hashlib.sha256).digest()
    
    payload = nonce + mac + encrypted_bytes
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def decrypt_data(encrypted_text: str) -> str:
    """
    Decrypts payload and verifies HMAC authenticity.
    """
    if not encrypted_text:
        return encrypted_text
    try:
        raw = base64.urlsafe_b64decode(encrypted_text.encode("utf-8"))
        if len(raw) < 48:  # 16 nonce + 32 mac
            return "[Invalid Payload]"
        
        nonce = raw[:16]
        mac = raw[16:48]
        encrypted_bytes = raw[48:]
        
        key = _get_derived_key()
        expected_mac = hmac.new(key, nonce + encrypted_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            return "[Integrity Check Failed]"
            
        expanded_keystream = b""
        counter = 0
        while len(expanded_keystream) < len(encrypted_bytes):
            expanded_keystream += hashlib.sha256(key + nonce + counter.to_bytes(4, "big")).digest()
            counter += 1
            
        decrypted_bytes = bytes([b ^ k for b, k in zip(encrypted_bytes, expanded_keystream)])
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return "[Decryption Error]"


def calculate_content_hash(text: Optional[str], caption: Optional[str] = None) -> str:
    """Calculates SHA-256 hash of normalized message text/caption."""
    normalized = f"{text or ''}|||{caption or ''}".strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()
