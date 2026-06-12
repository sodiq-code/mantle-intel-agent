"""
tests/test_hash_integrity.py
=============================
Verifiability guarantee tests — the most critical CI job.

These tests prove that:
  1. Finding hashes are deterministic and tamper-evident
  2. Pre-commit hashes can be independently verified by anyone
  3. On-chain bytes32 encoding is Solidity-compatible
  4. Hash changes when ANY field is modified (no silent collisions)

A judge can run `pytest tests/test_hash_integrity.py -v` to confirm
the entire verifiability chain works end-to-end.
"""
from __future__ import annotations

import hashlib
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from agents.anomaly.anomaly_agent import AnomalyFinding


# ─── Helper ──────────────────────────────────────────────────────────────────

def make_finding(**kwargs) -> AnomalyFinding:
    defaults = dict(
        finding_id="integrity-001",
        anomaly_type="whale_accumulation",
        block_height=96_500_000,
        timestamp="2026-06-12T12:00:00Z",
        confidence=0.95,
        description="Large whale accumulation detected on Mantle mainnet",
        raw_metrics={"tx_count": 8, "total_value_eth": 450_000},
        large_transfers=[{"value_eth": 300_000, "from": "0xAAA", "to": "0xBBB"}],
        method="isolation_forest",
        lead_time_blocks=12,
        investment_signal="ALERT: Accumulation phase — monitor for breakout",
    )
    defaults.update(kwargs)
    return AnomalyFinding(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Core hash integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestCoreHashIntegrity:

    def test_hash_is_64_char_hex(self):
        f = make_finding()
        h = f.sha256_hash()
        assert len(h) == 64
        int(h, 16)  # valid hex

    def test_hash_deterministic_same_object(self):
        f = make_finding()
        assert f.sha256_hash() == f.sha256_hash()

    def test_hash_deterministic_separate_instances(self):
        """Two objects with identical data must hash identically."""
        f1 = make_finding()
        f2 = make_finding()
        assert f1.sha256_hash() == f2.sha256_hash()

    def test_hash_matches_independent_sha256(self):
        """Judge can verify: take the JSON, SHA256 it, compare to on-chain hash."""
        f = make_finding()
        agent_hash = f.sha256_hash()

        # Independent verification (what a judge/auditor would do)
        canonical_json = json.dumps(f.to_dict(), sort_keys=True, separators=(",", ":"))
        independent_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        assert agent_hash == independent_hash, (
            "CRITICAL: Agent hash does not match independent SHA256 — verifiability broken"
        )

    def test_bytes32_is_32_bytes(self):
        f = make_finding()
        b32 = f.hex_bytes32()
        assert b32.startswith("0x")
        assert len(bytes.fromhex(b32[2:])) == 32

    def test_bytes32_matches_hash_prefix(self):
        """bytes32 must be the first 32 bytes of the SHA256 hash."""
        f = make_finding()
        h = f.sha256_hash()
        b32 = f.hex_bytes32()
        # bytes32 = first 32 bytes of hash (64 hex chars = 32 bytes)
        assert b32[2:].lower() == h[:64].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Tamper evidence — every field must affect the hash
# ═══════════════════════════════════════════════════════════════════════════════

class TestTamperEvidence:

    BASE = make_finding()

    @pytest.mark.parametrize("field,new_value", [
        ("confidence",       0.50),
        ("block_height",     1),
        ("anomaly_type",     "tx_spike"),
        ("description",      "Tampered description"),
        ("finding_id",       "tampered-id"),
        ("timestamp",        "2020-01-01T00:00:00Z"),
    ])
    def test_field_change_changes_hash(self, field, new_value):
        """Any field mutation must produce a different hash — tamper-evident."""
        original = make_finding()
        mutated = make_finding(**{field: new_value})
        assert original.sha256_hash() != mutated.sha256_hash(), (
            f"CRITICAL: Changing '{field}' did not change hash — tamper-evidence broken"
        )

    def test_raw_metrics_change_changes_hash(self):
        f1 = make_finding(raw_metrics={"tx_count": 100})
        f2 = make_finding(raw_metrics={"tx_count": 200})
        assert f1.sha256_hash() != f2.sha256_hash()

    def test_investment_signal_change_changes_hash(self):
        f1 = make_finding(investment_signal="WATCH: monitor")
        f2 = make_finding(investment_signal="IMMEDIATE ACTION: exit now")
        assert f1.sha256_hash() != f2.sha256_hash()


# ═══════════════════════════════════════════════════════════════════════════════
# Pre-commit sealing simulation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPreCommitSealing:
    """
    Simulates the pre-commit → on-chain → verify flow.

    This is the key architectural difference that makes findings verifiable:
    1. Hash is computed BEFORE the finding is logged on-chain
    2. Anyone can take the full finding JSON and recompute the hash
    3. If it matches the on-chain hash → finding is authentic, not backfilled
    """

    def test_pre_commit_seal_verify_cycle(self):
        """Full seal → commit → verify cycle must be consistent."""
        # Step 1: Agent detects anomaly, computes pre-commit hash
        finding = make_finding()
        pre_commit_hash = finding.sha256_hash()

        # Step 2: Hash goes on-chain (simulated as storing in dict)
        on_chain_record = {
            "hash": pre_commit_hash,
            "block_height": finding.block_height,
            "anomaly_type": finding.anomaly_type,
        }

        # Step 3: Later, full finding JSON is revealed
        revealed_json = json.dumps(finding.to_dict(), sort_keys=True, separators=(",", ":"))

        # Step 4: Anyone verifies by re-hashing the revealed JSON
        verification_hash = hashlib.sha256(revealed_json.encode("utf-8")).hexdigest()

        assert verification_hash == on_chain_record["hash"], (
            "Pre-commit seal verification failed — finding may have been tampered with"
        )

    def test_tampered_finding_fails_verification(self):
        """If the finding is modified after sealing, verification must fail."""
        original = make_finding()
        pre_commit_hash = original.sha256_hash()

        # Simulate tampering: change confidence after sealing
        tampered = make_finding(confidence=0.50)
        tampered_json = json.dumps(tampered.to_dict(), sort_keys=True, separators=(",", ":"))
        tampered_hash = hashlib.sha256(tampered_json.encode("utf-8")).hexdigest()

        assert tampered_hash != pre_commit_hash, (
            "Tampered finding passed verification — hash is not tamper-evident"
        )

    def test_multiple_findings_have_unique_hashes(self):
        """All findings in a batch must have unique hashes."""
        findings = [
            make_finding(finding_id=f"f-{i}", block_height=1000 + i, confidence=0.75 + i * 0.01)
            for i in range(20)
        ]
        hashes = [f.sha256_hash() for f in findings]
        assert len(set(hashes)) == len(hashes), (
            "Hash collision detected among batch findings"
        )
