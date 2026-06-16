#!/usr/bin/env python3
"""Build the published JWKS for a2-Sign verification, from keys/*.pem.

Output: keys/v1/jwks.json (+ metadata.json). Verifiers fetch a public key by
`kid` from https://a2-schema.org/keys/v1/jwks.json (the `jku` the signer writes).
RSA/ECDSA → standard RFC 7517 JWKs; ML-DSA → draft-ietf-jose-pqc "AKP" key type.

Run: ./.venv/bin/python tools/build_jwks.py   (needs `cryptography`)
"""
import base64
import json
import os

from cryptography.hazmat.primitives import serialization

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEYS = os.path.join(ROOT, "keys")
OUT = os.path.join(KEYS, "v1")
JKU = "https://a2-schema.org/keys/v1/jwks.json"


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def load(name: str):
    with open(os.path.join(KEYS, name), "rb") as f:
        return serialization.load_pem_public_key(f.read())


def ec_jwk(pub) -> dict:
    n = pub.public_numbers()
    size = (pub.curve.key_size + 7) // 8
    return {"kty": "EC", "crv": "P-256", "x": b64u(n.x.to_bytes(size, "big")),
            "y": b64u(n.y.to_bytes(size, "big"))}


def rsa_jwk(pub) -> dict:
    n = pub.public_numbers()
    return {"kty": "RSA", "n": b64u(n.n.to_bytes((n.n.bit_length() + 7) // 8, "big")),
            "e": b64u(n.e.to_bytes((n.e.bit_length() + 7) // 8, "big"))}


def mldsa_jwk(pub) -> dict:
    # FIPS 204 raw public key (1952 B for ML-DSA-65), JOSE draft "AKP" key type.
    try:
        raw = pub.public_bytes_raw()
    except AttributeError:
        raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return {"kty": "AKP", "alg": "ML-DSA-65", "pub": b64u(raw)}


KEY_SPECS = [
    ("ml-dsa-65-v1", "ML-DSA-65", "ml-dsa-public.pem", mldsa_jwk),
    ("es256-v1", "ES256", "ecdsa-public.pem", ec_jwk),
    ("rs256-v1", "RS256", "rsa-public.pem", rsa_jwk),
]

keys = []
for kid, alg, pem, to_jwk in KEY_SPECS:
    jwk = to_jwk(load(pem))
    jwk.update({"kid": kid, "use": "sig", "alg": alg})
    keys.append(jwk)
    print(f"  {kid:14} {alg:9} {jwk['kty']}")

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "jwks.json"), "w") as f:
    json.dump({"keys": keys}, f, indent=2)
with open(os.path.join(OUT, "metadata.json"), "w") as f:
    json.dump({
        "jku": JKU,
        "issuer": "a2-Sign / Ichiri",
        "keys": [{"kid": k, "alg": a, "pem": f"https://a2-schema.org/keys/{p}"} for k, a, p, _ in KEY_SPECS],
        "note": "ML-DSA-65 uses the JOSE PQC draft 'AKP' key type (FIPS 204 raw public key).",
    }, f, indent=2, ensure_ascii=False)
print(f"wrote {OUT}/jwks.json + metadata.json  ({len(keys)} keys)")
