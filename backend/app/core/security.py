"""

Password hashing + verification.

We are using Argon2 (recommended) for server-side password hashing.
If your frontend later does SHA256(password) before sending, that's fine,
but the server still must Argon2-hash the received value.

Important:
- Never store plaintext passwords.
- Never log passwords.
- Hashing twice on the server is pointless.

TODO:
- if team insists on bcrypt instead, swap implementation here only.
"""

import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def sha256_hex(value: str) -> str:
    """Client-side style hashing helper (optional)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_secret(secret: str) -> str:
    """Store this in DB."""
    return _ph.hash(secret)


def verify_secret(secret: str, stored_hash: str) -> bool:
    """Check login password vs stored hash."""
    try:
        return _ph.verify(stored_hash, secret)
    except VerifyMismatchError:
        return False
