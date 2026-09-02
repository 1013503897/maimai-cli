"""
Pure-Python reproduction of 脉脉's client-side crypto — re.C6584 (DigestUtils.kt) — used at login.

Unlike BOSS直聘, 脉脉 has NO per-request request signature; the only client crypto that touches
the network path is at login, where the *password* field is RSA-encrypted:

    epassword = base64_nowrap( RSA/ECB/PKCS1Padding( pubkey = NativeLib.getKey(), utf8(password) ) )

`NativeLib.getKey()` (native, libnativelib_maimai.so) returns an RSA **public** key (X.509 DER,
base64) — it is public, not a secret, so it can simply be captured/extracted once and pasted into
the session file. SMS-code login needs none of this (only the password path uses epassword).

md5 / sha1 / sha256 are the other DigestUtils branches, provided for parity / tests.
"""
from __future__ import annotations
import base64
import hashlib

# The RSA public key NativeLib.getKey() returns on v6.6.84 — captured live via frida (a 1024-bit
# X.509 SubjectPublicKeyInfo, base64). It's a *public* key, not a secret; login.py uses it as the
# default for password login when the session doesn't override it. May rotate across app versions.
MAIMAI_LOGIN_PUBKEY = (
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDbJGJuNnD/h1Cnrjw4rwjQ9JXZssXgpsjPrhPzn0BQ+04a"
    "WHHTkEFopyqMOaSz35fAlGt8jcRDxYIE4q5/2/xHlPNczkPJUZJ2hkzqPTnhlNu8aLasFxdrgZrBZEIWrnFkt"
    "IoIiGMqzuVQ5ZBsGGc9GQg36Mbx2Wuj3m5MzRq6awIDAQAB")

# The DigestUtils algorithm-string dispatcher (re.C6584.ൡ) understands these.
ALG_RSA = "RSA"
ALG_MD5 = "MD5"
ALG_SHA1 = "SHA-1"
ALG_SHA256 = "SHA-256"


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def encrypt_password(plaintext: str, pubkey_b64: str) -> str:
    """epassword = base64(RSA/ECB/PKCS1Padding(pubkey, plaintext)). Mirrors the RSA branch of
    re.C6584 (X509EncodedKeySpec -> KeyFactory("RSA") -> Cipher("RSA/ECB/PKCS1Padding") ->
    Base64.NO_WRAP). Needs pycryptodome (`pip install '.[login]'`); pubkey_b64 is getKey()."""
    try:
        from Crypto.Cipher import PKCS1_v1_5
        from Crypto.PublicKey import RSA
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "password login needs pycryptodome: pip install 'maimai-cli[login]'") from e
    der = base64.b64decode(pubkey_b64)
    key = RSA.import_key(der)
    cipher = PKCS1_v1_5.new(key)
    enc = cipher.encrypt(plaintext.encode("utf-8"))
    return base64.b64encode(enc).decode("ascii")


def digest(algorithm: str, plaintext: str, key: str = "") -> str:
    """Dispatch like re.C6584.ൡ(bytes, algorithm, key): RSA uses `key` as the pubkey; the
    digests ignore it."""
    if algorithm == ALG_RSA:
        return encrypt_password(plaintext, key)
    if algorithm == ALG_MD5:
        return md5_hex(plaintext)
    if algorithm == ALG_SHA1:
        return sha1_hex(plaintext)
    if algorithm == ALG_SHA256:
        return sha256_hex(plaintext)
    raise ValueError(f"unsupported algorithm: {algorithm!r}")
