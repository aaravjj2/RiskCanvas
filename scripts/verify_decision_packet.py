#!/usr/bin/env python3
"""
scripts/verify_decision_packet.py (v5.46.0 — Wave 57)

Offline CLI verifier for signed Decision Packets.

Usage:
    python scripts/verify_decision_packet.py <packet_id> [--public-key <hex>]

Reads from the live API (http://localhost:8090) to fetch the packet and
its signature record, then verifies the Ed25519 signature offline.

Exit 0 = verified OK
Exit 1 = verification failed or error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from typing import Any, Dict

API_BASE = "http://localhost:8090"


def _http_get(path: str) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Could not reach API at {url}: {e}")
        sys.exit(1)


def verify_packet_offline(packet_id: str, public_key_hex: str | None = None) -> int:
    """
    Fetch packet + signature from API, then verify offline.
    Returns 0 (OK) or 1 (FAIL).
    """
    # Fetch packet
    try:
        packet_resp = _http_get(f"/exports/decision-packets/{packet_id}")
    except SystemExit:
        print(f"FAIL: Could not fetch packet {packet_id}")
        return 1

    packet = packet_resp.get("packet", packet_resp)
    manifest_hash = packet.get("manifest_hash", "")
    files = packet.get("files", {})

    # Fetch signature
    try:
        sig_resp = _http_get(f"/signatures/{packet_id}")
    except SystemExit:
        print(f"FAIL: No signature record for packet {packet_id}")
        return 1

    sig = sig_resp.get("signature", sig_resp)
    stored_signature_hex = sig.get("signature", "")
    stored_public_key = public_key_hex or sig.get("public_key", "")
    stored_manifest_hash = sig.get("manifest_hash", "")
    signed_at = sig.get("signed_at", "")

    # Verify
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        canonical_payload = json.dumps(
            {
                "packet_id": packet_id,
                "manifest_hash": stored_manifest_hash,
                "files": dict(sorted(files.items())) if isinstance(files, dict) else files,
                "signed_at": signed_at,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode()

        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(stored_public_key))
        pubkey.verify(bytes.fromhex(stored_signature_hex), canonical_payload)
        verified = True
        error = None
    except Exception as e:
        verified = False
        error = str(e)

    # Manifest hash check
    if verified and manifest_hash != stored_manifest_hash:
        verified = False
        error = f"manifest_hash mismatch: packet={manifest_hash[:16]}... signed={stored_manifest_hash[:16]}..."

    # Output
    print(f"=== RiskCanvas Decision Packet Verifier ===")
    print(f"Packet ID:      {packet_id}")
    print(f"Algorithm:      Ed25519")
    print(f"Public Key:     {stored_public_key[:16]}...{stored_public_key[-8:]}")
    print(f"Manifest Hash:  {manifest_hash[:16]}...{manifest_hash[-8:]}")
    print(f"Signed At:      {signed_at}")
    print()

    if verified:
        print("✓  VERIFICATION PASSED — signature is valid, packet is untampered")
        return 0
    else:
        print(f"✗  VERIFICATION FAILED — {error}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Decision Packet Verifier")
    parser.add_argument("packet_id", help="ID of the decision packet to verify")
    parser.add_argument(
        "--public-key",
        help="Optional: override public key (hex) for verification",
        default=None,
    )
    parser.add_argument(
        "--api-base",
        help=f"API base URL (default: {API_BASE})",
        default=None,
    )
    args = parser.parse_args()

    global API_BASE
    if args.api_base:
        API_BASE = args.api_base

    return verify_packet_offline(args.packet_id, args.public_key)


if __name__ == "__main__":
    sys.exit(main())
