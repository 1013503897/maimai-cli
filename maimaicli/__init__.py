"""maimai-cli — off-device 脉脉 (com.taou.maimai) API client, pure Python.

Reverse-engineered from com.taou.maimai v6.6.84. Unlike BOSS直聘 (libyzwg sp/sig), 脉脉
adds NO per-request native signature: every API request is authenticated by an account
`access_token` + `u`(uid) plus a set of plaintext device-fingerprint query params, all sent
over TLS. So once a session is captured (or minted via `mm login`), a plain HTTP request is
accepted by the server — this package just assembles that request faithfully.
"""
__version__ = "0.1.0"
