"""
packet_signing.py (v5.46.0 — Wave 57)

Ed25519 offline signing for Decision Packets.

Provides:
  - sign_packet(packet_id, files_content) → signature record
  - verify_signed_packet(packet_id) → verification result
  - get_signing_key() → deterministic demo key pair (DEMO mode)

DEMO mode: uses a deterministic private key seeded from DEMO constant.
Production: set SIGNING_KEY_HEX env var to a 32-byte hex private key.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
SIGNING_ALG = "Ed25519"

# In-memory store: packet_id → signature record
SIGNATURE_STORE: Dict[str, Dict[str, Any]] = {}


# ── Key management ────────────────────────────────────────────────────────────


def _get_demo_private_key_bytes() -> bytes:
    """Deterministic 32 bytes derived from the DEMO constant (offline, reproducible)."""
    seed = hashlib.sha256(
        f"riskcanvas-demo-signing-key-{ASOF}".encode()
    ).digest()
    return seed  # 32 bytes = valid Ed25519 private key seed


def get_signing_key() -> Ed25519PrivateKey:
    """
    Return the Ed25519 private key.
    DEMO mode: deterministic from ASOF constant.
    Production: from SIGNING_KEY_HEX env var (32-byte hex).
    """
    hex_key = os.environ.get("SIGNING_KEY_HEX", "")
    if hex_key:
        seed = bytes.fromhex(hex_key)
    else:
        seed = _get_demo_private_key_bytes()
    return Ed25519PrivateKey.from_private_bytes(seed)


def _private_as_hex(privkey: Ed25519PrivateKey) -> str:
    raw = privkey.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    return raw.hex()


def _public_as_hex(pubkey: Ed25519PublicKey) -> str:
    raw = pubkey.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return raw.hex()


# ── Core sign / verify ────────────────────────────────────────────────────────


def sign_packet(
    packet_id: str,
    manifest_hash: str,
    files: Dict[str, str],  # filename → hash
    signed_by: str = "demo-signer@riskcanvas.io",
) -> Dict[str, Any]:
    """
    Sign a decision packet's manifest hash with Ed25519.

    Returns a signature record stored in SIGNATURE_STORE.
    """
    privkey = get_signing_key()
    pubkey = privkey.public_key()

    # Build canonical payload to sign
    canonical_payload = json.dumps(
        {
            "packet_id": packet_id,
            "manifest_hash": manifest_hash,
            "files": dict(sorted(files.items())),
            "signed_at": ASOF,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()

    # Sign
    signature_bytes = privkey.sign(canonical_payload)
    signature_hex = signature_bytes.hex()
    public_key_hex = _public_as_hex(pubkey)

    record = {
        "packet_id": packet_id,
        "algorithm": SIGNING_ALG,
        "public_key": public_key_hex,
        "signature": signature_hex,
        "payload_hash": hashlib.sha256(canonical_payload).hexdigest(),
        "manifest_hash": manifest_hash,
        "signed_by": signed_by,
        "signed_at": ASOF,
        "files": files,
    }

    SIGNATURE_STORE[packet_id] = record
    return record


def verify_signed_packet(
    packet_id: str,
    manifest_hash: str,
    files: Dict[str, str],
) -> Dict[str, Any]:
    """
    Verify the Ed25519 signature for a signed decision packet.

    Returns a verification result dict including `verified: bool`.
    Tamper detection: if files or manifest_hash differ from signed record, fails.
    """
    if packet_id not in SIGNATURE_STORE:
        return {
            "packet_id": packet_id,
            "verified": False,
            "error": "No signature found for packet_id",
            "verified_at": ASOF,
        }

    record = SIGNATURE_STORE[packet_id]

    # Reconstruct canonical payload
    canonical_payload = json.dumps(
        {
            "packet_id": packet_id,
            "manifest_hash": manifest_hash,
            "files": dict(sorted(files.items())),
            "signed_at": ASOF,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()

    try:
        pubkey_bytes = bytes.fromhex(record["public_key"])
        pubkey = Ed25519PublicKey.from_public_bytes(pubkey_bytes)
        sig_bytes = bytes.fromhex(record["signature"])
        pubkey.verify(sig_bytes, canonical_payload)
        verified = True
        error = None
    except Exception as e:
        verified = False
        error = str(e)

    # Also check manifest hash matches
    if verified and manifest_hash != record["manifest_hash"]:
        verified = False
        error = "manifest_hash mismatch — packet may have been tampered"

    return {
        "packet_id": packet_id,
        "verified": verified,
        "algorithm": SIGNING_ALG,
        "public_key": record["public_key"],
        "manifest_hash": manifest_hash,
        "signed_manifest_hash": record["manifest_hash"],
        "error": error,
        "signed_by": record["signed_by"],
        "signed_at": record["signed_at"],
        "verified_at": ASOF,
    }


def get_signature(packet_id: str) -> Dict[str, Any]:
    """Retrieve the stored signature record for a packet."""
    if packet_id not in SIGNATURE_STORE:
        raise ValueError(f"No signature for packet: {packet_id}")
    return SIGNATURE_STORE[packet_id]


def list_signatures() -> list:
    return list(SIGNATURE_STORE.values())


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/signatures", tags=["signatures"])


class SignPacketRequest(BaseModel):
    packet_id: str
    manifest_hash: str
    files: Dict[str, str]
    signed_by: str = "demo-signer@riskcanvas.io"


class VerifySignatureRequest(BaseModel):
    manifest_hash: str
    files: Dict[str, str]


@router.post("/sign")
def http_sign_packet(req: SignPacketRequest):
    record = sign_packet(
        packet_id=req.packet_id,
        manifest_hash=req.manifest_hash,
        files=req.files,
        signed_by=req.signed_by,
    )
    return {"signature": record}


@router.get("/")
def http_list_signatures():
    return {"signatures": list_signatures()}


@router.get("/{packet_id}")
def http_get_signature(packet_id: str):
    try:
        return {"signature": get_signature(packet_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{packet_id}/verify")
def http_verify_signature(packet_id: str, req: VerifySignatureRequest):
    result = verify_signed_packet(
        packet_id=packet_id,
        manifest_hash=req.manifest_hash,
        files=req.files,
    )
    return result
