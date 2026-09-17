"""
Runtime Lane-1 commit authorization boundary tests.

Task: PH6-RUNTIME-LANE-1-AUTHORIZATION-BOUNDARY (2026-09-15). Proves the
specific, previously-certified stop-ship defect (AI_ADVISORY-003 /
PSEUDO-SEAM-001, PH6-CERTIFICATION-RECEIPT.json, generated 2026-09-05) is
closed: both real production commit paths --
`CRAMWriter.commit()` (crash_replay.py) and `AtomicCRAMCommitter.commit()`
(tools/cram_pu_atomic_commit.py) -- now require and verify a Lane-1
commit authorization object (ph6.cram_pu._lane1_auth) before any
filesystem write, and no caller-supplied field (`authority`, `verdict`,
or any hand-shaped authorization-looking dict) can substitute for it.

Every "attacker" below is a plain, synthetic caller -- exactly the
AI_ADVISORY-003 attack shape -- labeled per the component whose identity
it claims, to satisfy the required negative-path matrix (SoSo, TOK,
SoSo-JEDI, BCV2, JEDI Master, T0, T1, T2, AI, NERO). None of these
components actually import CRAMWriter/AtomicCRAMCommitter in real
production code (confirmed separately by the Lane-2 advisory tree's own
reverse-path static proof, elsewhere in this repository) -- these tests
establish what would happen if one did, which is the actual runtime
property this task requires, not merely "no one currently does."
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from ph6.cram_pu.crash_replay import CRAMWriter
from ph6.cram_pu.tools.cram_pu_atomic_commit import AtomicCRAMCommitter, commit_pass_verdicts
from ph6.cram_pu._lane1_auth import (
    LaneOneAuthorizationError,
    mint_commit_authorization,
    verify_commit_authorization,
)

# Every Lane-2 / advisory / AI identity named in the task's required
# negative-path matrix. Each is used only as a label on a synthetic
# attacker call -- none of these are real imports of those components.
LANE2_CALLER_IDENTITIES = [
    "SoSo", "TOK", "SoSo-JEDI", "BCV2", "JEDI_Master",
    "T0", "T1", "T2", "AI", "NERO",
]


def _verdict(frame_id: int = 1, verdict: str = "PASS") -> dict:
    return {
        "schema": "ph6.pseudo_verdict.v1",
        "frame_id": frame_id,
        "verdict": verdict,
        "metrics": {"entropy_fp": 31000, "laplacian_var_fp": 800000, "motion_fraction_fp": 200},
        "reasons": [],
        "authority": "LANE_1",
    }


def _snapshot(cram_dir: Path) -> dict:
    """Directory-state fingerprint: filenames + exact byte content of every
    committed record and every .blake2b marker. Used for the CRAM-A
    before/after integrity proof -- not merely "no exception raised"."""
    out = {}
    for p in sorted(cram_dir.iterdir()):
        out[p.name] = p.read_bytes()
    return out


# ---------------------------------------------------------------------------
# A. Positive path: a real Lane-1-minted authorization still works
# ---------------------------------------------------------------------------

class TestPositivePathStillWorks:
    def test_cram_writer_accepts_genuine_authorization(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        auth = mint_commit_authorization(frame_id=1, payload_hash="h" * 64, verdict="PASS")

        record = writer.commit(1, "h" * 64, verd, auth)

        assert record["cram_hash"]
        assert (tmp_path / "cram_0000000001.json").exists()
        assert (tmp_path / "cram_0000000001.json.blake2b").exists()

    def test_atomic_cram_committer_accepts_genuine_authorization(self, tmp_path):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {"packet_id": "pkt_pos_001", "input_hash": "h" * 64, "verdict": "PASS"}
        auth = mint_commit_authorization(packet_id="pkt_pos_001", payload_hash="h" * 64, verdict="PASS")

        record = committer.commit(verdict, auth)

        assert record["cram_hash"]
        assert list(tmp_path.glob("*.blake2b"))

    def test_commit_pass_verdicts_still_mints_and_succeeds(self, tmp_path):
        verdicts = [{"packet_id": "pkt_p1", "input_hash": "h" * 64, "verdict": "PASS"}]
        committed = commit_pass_verdicts(verdicts, tmp_path)
        assert len(committed) == 1
        assert list(tmp_path.glob("*.blake2b"))


# ---------------------------------------------------------------------------
# B. Negative path: every Lane-2/AI identity, unauthorized commit -> REJECT
# ---------------------------------------------------------------------------

class TestNegativePathCramWriter:
    @pytest.mark.parametrize("caller", LANE2_CALLER_IDENTITIES)
    def test_no_authorization_object_is_rejected(self, tmp_path, caller):
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        verd["claimed_caller"] = caller  # provenance label only; never trusted

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, None)

        assert list(tmp_path.glob("cram_*.json")) == []

    @pytest.mark.parametrize("caller", LANE2_CALLER_IDENTITIES)
    def test_self_declared_authority_field_does_not_substitute(self, tmp_path, caller):
        """The exact AI_ADVISORY-003 shape: a caller-constructed dict
        already claims authority="LANE_1" and verdict="PASS" inside the
        verdict_record itself -- that must not be read as authorization."""
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        verd["authority"] = "LANE_1"
        verd["claimed_caller"] = caller

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, {"authority": "LANE_1", "claimed_caller": caller})

        assert list(tmp_path.glob("cram_*.json")) == []

    @pytest.mark.parametrize("caller", LANE2_CALLER_IDENTITIES)
    def test_hand_forged_authorization_shape_is_rejected(self, tmp_path, caller):
        """Plausible-looking authorization object (right schema, right
        field names) but no valid MAC -- proves fields alone (without a
        MAC that verifies against the live secret) grant nothing."""
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        forged = {
            "schema": "ph6.lane1_commit_authorization.v1",
            "fields": {"frame_id": 1, "payload_hash": "h" * 64, "verdict": "PASS"},
            "mac": "0" * 64,
            "issued_by": caller,
        }

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, forged)

        assert list(tmp_path.glob("cram_*.json")) == []

    def test_authorization_minted_for_different_frame_id_is_rejected(self, tmp_path):
        """Binding proof: a genuinely-minted authorization for frame_id=2
        cannot be replayed against frame_id=1's commit request."""
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        auth_for_other_frame = mint_commit_authorization(frame_id=2, payload_hash="h" * 64, verdict="PASS")

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, auth_for_other_frame)

        assert list(tmp_path.glob("cram_*.json")) == []

    def test_authorization_minted_for_different_payload_hash_is_rejected(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        auth_for_other_payload = mint_commit_authorization(frame_id=1, payload_hash="z" * 64, verdict="PASS")

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, auth_for_other_payload)

        assert list(tmp_path.glob("cram_*.json")) == []

    def test_tampered_mac_on_otherwise_genuine_authorization_is_rejected(self, tmp_path):
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        auth = mint_commit_authorization(frame_id=1, payload_hash="h" * 64, verdict="PASS")
        auth = dict(auth, mac=auth["mac"][:-1] + ("0" if auth["mac"][-1] != "0" else "1"))

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, auth)

        assert list(tmp_path.glob("cram_*.json")) == []

    def test_authorization_from_wrong_object_shape_is_rejected(self, tmp_path):
        """A TOK/SoSo/SwarmPacket-style advisory object substituted directly
        as the authorization argument -- schema mismatch, not a value the
        MAC check even reaches."""
        writer = CRAMWriter(tmp_path)
        verd = _verdict(1)
        soso_style_packet = {
            "schema": "ph6.ssmt.swarm_packet.v1",
            "authority": "NONE",
            "swarm_id": "S1",
        }

        with pytest.raises(LaneOneAuthorizationError):
            writer.commit(1, "h" * 64, verd, soso_style_packet)

        assert list(tmp_path.glob("cram_*.json")) == []


class TestNegativePathAtomicCramCommitter:
    @pytest.mark.parametrize("caller", LANE2_CALLER_IDENTITIES)
    def test_no_authorization_object_is_rejected(self, tmp_path, caller):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {"packet_id": f"pkt_{caller}", "input_hash": "h" * 64, "verdict": "PASS"}

        with pytest.raises(LaneOneAuthorizationError):
            committer.commit(verdict, None)

        assert list(tmp_path.glob("cram_*.json")) == []

    @pytest.mark.parametrize("caller", LANE2_CALLER_IDENTITIES)
    def test_hand_forged_authorization_is_rejected(self, tmp_path, caller):
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {"packet_id": f"pkt_{caller}", "input_hash": "h" * 64, "verdict": "PASS"}
        forged = {
            "schema": "ph6.lane1_commit_authorization.v1",
            "fields": {"packet_id": f"pkt_{caller}", "payload_hash": "h" * 64, "verdict": "PASS"},
            "mac": "f" * 64,
        }

        with pytest.raises(LaneOneAuthorizationError):
            committer.commit(verdict, forged)

        assert list(tmp_path.glob("cram_*.json")) == []

    def test_authorization_from_cram_writer_field_shape_does_not_cross_apply(self, tmp_path):
        """A genuinely-minted CRAMWriter-shaped authorization (frame_id
        key) must not satisfy AtomicCRAMCommitter's field shape
        (packet_id key) -- proves the two commit classes' authorizations
        are not interchangeable."""
        committer = AtomicCRAMCommitter(tmp_path)
        verdict = {"packet_id": "pkt_cross", "input_hash": "h" * 64, "verdict": "PASS"}
        cram_writer_shaped_auth = mint_commit_authorization(frame_id=1, payload_hash="h" * 64, verdict="PASS")

        with pytest.raises(LaneOneAuthorizationError):
            committer.commit(verdict, cram_writer_shaped_auth)

        assert list(tmp_path.glob("cram_*.json")) == []


# ---------------------------------------------------------------------------
# C. CRAM-A before/after integrity proof
# ---------------------------------------------------------------------------

class TestCramABeforeAfterIntegrity:
    def test_cram_a_unchanged_after_full_negative_campaign(self, tmp_path):
        writer = CRAMWriter(tmp_path)

        # Establish one legitimate PASS commit as the protected "before" state.
        genuine_auth = mint_commit_authorization(frame_id=1, payload_hash="h" * 64, verdict="PASS")
        writer.commit(1, "h" * 64, _verdict(1), genuine_auth)

        before = _snapshot(tmp_path)
        before_prev_hash = writer._prev_hash
        assert before  # sanity: the one genuine record + marker exist

        # Run every unauthorized-commit attack, for every claimed identity,
        # against a *second* frame_id -- none may succeed or alter anything
        # already on disk.
        attacks = []
        for caller in LANE2_CALLER_IDENTITIES:
            attacks.append((None,))
            attacks.append(({"authority": "LANE_1", "claimed_caller": caller},))
            attacks.append(({
                "schema": "ph6.lane1_commit_authorization.v1",
                "fields": {"frame_id": 2, "payload_hash": "h" * 64, "verdict": "PASS"},
                "mac": "0" * 64,
            },))

        rejected = 0
        for (bad_auth,) in attacks:
            try:
                writer.commit(2, "h" * 64, _verdict(2), bad_auth)
            except LaneOneAuthorizationError:
                rejected += 1
            else:
                pytest.fail("an unauthorized commit attempt succeeded")

        assert rejected == len(attacks)

        after = _snapshot(tmp_path)
        assert after == before, "CRAM-A directory state changed after an unauthorized-commit campaign"
        assert writer._prev_hash == before_prev_hash, "chain state (_prev_hash) advanced without an authorized commit"
        assert list(tmp_path.glob("cram_*.json")) == [tmp_path / "cram_0000000001.json"]

    def test_legitimate_commit_still_succeeds_after_negative_campaign(self, tmp_path):
        """Proves the boundary fails closed, not merely 'exception raised
        somewhere' -- a real Lane-1-authorized commit for the next frame
        still succeeds immediately afterward."""
        writer = CRAMWriter(tmp_path)
        genuine_auth_1 = mint_commit_authorization(frame_id=1, payload_hash="h" * 64, verdict="PASS")
        writer.commit(1, "h" * 64, _verdict(1), genuine_auth_1)

        for caller in LANE2_CALLER_IDENTITIES:
            try:
                writer.commit(2, "h" * 64, _verdict(2), {"claimed_caller": caller})
            except LaneOneAuthorizationError:
                pass

        genuine_auth_2 = mint_commit_authorization(frame_id=2, payload_hash="h" * 64, verdict="PASS")
        record2 = writer.commit(2, "h" * 64, _verdict(2), genuine_auth_2)

        assert record2["prev_cram_hash"] == json.loads(
            (tmp_path / "cram_0000000001.json").read_text()
        )["cram_hash"]
        assert (tmp_path / "cram_0000000002.json.blake2b").exists()


# ---------------------------------------------------------------------------
# D. verify_commit_authorization unit-level checks (direct, no I/O)
# ---------------------------------------------------------------------------

class TestVerifyCommitAuthorizationDirect:
    def test_wrong_type_rejected(self):
        with pytest.raises(LaneOneAuthorizationError):
            verify_commit_authorization("not-a-dict", frame_id=1, payload_hash="h", verdict="PASS")

    def test_missing_mac_rejected(self):
        with pytest.raises(LaneOneAuthorizationError):
            verify_commit_authorization(
                {"schema": "ph6.lane1_commit_authorization.v1", "fields": {"frame_id": 1}},
                frame_id=1,
            )

    def test_genuine_mint_verifies(self):
        auth = mint_commit_authorization(frame_id=5, payload_hash="q" * 64, verdict="PASS")
        verify_commit_authorization(auth, frame_id=5, payload_hash="q" * 64, verdict="PASS")  # no raise

    def test_extra_unexpected_field_rejected(self):
        auth = mint_commit_authorization(frame_id=5, payload_hash="q" * 64, verdict="PASS")
        with pytest.raises(LaneOneAuthorizationError):
            verify_commit_authorization(auth, frame_id=5, payload_hash="q" * 64, verdict="PASS", extra="x")
