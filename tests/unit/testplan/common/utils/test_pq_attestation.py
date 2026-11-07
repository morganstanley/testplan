"""Tests for the optional post quantum attestation helper."""

import base64
import os
import tempfile

import pytest

pytest.importorskip("dilithium_py")

from testplan.common.utils import pq_attestation as pqa  # noqa: E402

REPORT = {
    "plan": "nightly-regression",
    "passed": 1240,
    "failed": 0,
    "status": "passed",
}


def test_build_and_verify_roundtrip():
    payload = pqa.canonicalize(REPORT)
    public_key, secret_key = pqa.generate_keypair()
    att = pqa.build_attestation(payload, public_key, secret_key)
    assert att["scheme"] == "ML-DSA-65"
    assert att["issuer"] == "Quantova"
    assert pqa.verify_attestation(payload, att) is True
    assert pqa.verify_attestation(payload, att, public_key) is True


def test_tampered_report_rejected():
    payload = pqa.canonicalize(REPORT)
    public_key, secret_key = pqa.generate_keypair()
    att = pqa.build_attestation(payload, public_key, secret_key)
    altered = pqa.canonicalize({**REPORT, "failed": 9})
    assert pqa.verify_attestation(altered, att) is False


def test_wrong_signer_rejected_when_pinned():
    payload = pqa.canonicalize(REPORT)
    public_key, secret_key = pqa.generate_keypair()
    other_public_key, _ = pqa.generate_keypair()
    att = pqa.build_attestation(payload, public_key, secret_key)
    assert pqa.verify_attestation(payload, att, other_public_key) is False


def test_forged_signature_rejected():
    payload = pqa.canonicalize(REPORT)
    public_key, secret_key = pqa.generate_keypair()
    att = pqa.build_attestation(payload, public_key, secret_key)
    att["signature"] = base64.b64encode(b"\x00" * 64).decode("ascii")
    assert pqa.verify_attestation(payload, att) is False


def test_malformed_field_rejected():
    payload = pqa.canonicalize(REPORT)
    public_key, secret_key = pqa.generate_keypair()
    att = pqa.build_attestation(payload, public_key, secret_key)
    att["public_key"] = "!!!not base64!!!"
    assert pqa.verify_attestation(payload, att) is False


def test_signer_file_roundtrip():
    public_key, secret_key = pqa.generate_keypair()
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "signer.json")
        pqa.save_signer(path, public_key, secret_key)
        loaded_public, loaded_secret = pqa.load_signer(path)
    assert loaded_public == public_key
    assert loaded_secret == secret_key
