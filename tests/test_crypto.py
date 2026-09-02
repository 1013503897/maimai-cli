"""Login crypto — DigestUtils (re.C6584) reproduction."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from maimaicli import crypto


def test_md5():
    assert crypto.md5_hex("abc") == "900150983cd24fb0d6963f7d28e17f72"


def test_sha256():
    assert crypto.sha256_hex("abc") == \
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_password_rsa_roundtrip():
    """epassword = base64(RSA/ECB/PKCS1(pubkey, password)); decrypt with the matching private
    key must recover the plaintext. Skips cleanly if pycryptodome isn't installed."""
    try:
        import base64
        from Crypto.Cipher import PKCS1_v1_5
        from Crypto.PublicKey import RSA
    except ImportError:
        print("  skip test_password_rsa_roundtrip (pycryptodome not installed)")
        return
    key = RSA.generate(2048)
    pub_b64 = base64.b64encode(key.publickey().export_key(format="DER")).decode()
    epwd = crypto.encrypt_password("s3cr3t!", pub_b64)
    dec = PKCS1_v1_5.new(key).decrypt(base64.b64decode(epwd), None)
    assert dec == b"s3cr3t!"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print(f"  ok  {name}"); n += 1
    print(f"all {n} tests passed")
