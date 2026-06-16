#!/usr/bin/env python3
"""
Boundary tests for Desktop Patch 1 — Device Manager + Device Registry +
Test Breakdown Viewer.

Authority: ZERO. These tests prove the new panels stay inside the Class 3
envelope defined in PH6_DESKTOP_CLASS3_PROTOTYPE_DOCTRINE_v1.1.md:
  - new devices default to STATUS: UNVERIFIED
  - Desktop never fabricates PASS/DROP verdicts
  - Desktop never writes into CRAM paths
  - the Test Breakdown viewer is read-only over existing artifacts
"""
import builtins
import importlib.util
import inspect
import json
import unittest
from pathlib import Path

_TERMINAL_PATH = Path(__file__).resolve().parents[1] / "ph6_desktop_terminal.py"


def _load_terminal_module():
    spec = importlib.util.spec_from_file_location("ph6_desktop_terminal_under_test", _TERMINAL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestDeviceRegistryDefaultsUnverified(unittest.TestCase):
    def setUp(self):
        self.mod = _load_terminal_module()

    def test_seed_registry_file_is_non_authoritative_with_unverified_devices(self):
        reg_path = Path(__file__).resolve().parents[1] / "device_registry.json"
        self.assertTrue(reg_path.exists(), "device_registry.json missing")
        reg = json.loads(reg_path.read_text())
        self.assertEqual(reg.get("authority"), "ZERO")
        self.assertTrue(reg.get("non_authoritative") is True)
        # Phase B onboarding populates the registry with UNVERIFIED Authority
        # ZERO entries (Zero 2W sentinel, Pico sensor node) — every entry,
        # whatever its origin, must default to UNVERIFIED / unreviewed.
        for entry in reg.get("devices", []):
            self.assertEqual(entry.get("status"), "UNVERIFIED")
            self.assertEqual(entry.get("authority"), "ZERO")
            self.assertFalse(entry.get("operator_reviewed"))
            self.assertIsNone(entry.get("probe_result"))

    def test_new_device_registration_defaults_to_unverified(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp_registry = Path(td) / "device_registry.json"
            tmp_registry.write_text(json.dumps({
                "schema": "ph6.desktop.device_registry.v1",
                "authority": "ZERO",
                "non_authoritative": True,
                "devices": [],
            }))

            self.mod._DEVICE_REGISTRY_JSON = tmp_registry
            self.mod._ACCESS_MODE = "CONTROL"

            answers = iter(["y", "Test Camera", "camera"])
            self.mod.input = lambda *_a, **_k: next(answers)        # type: ignore[attr-defined]
            self.mod._pause = lambda: None                           # type: ignore[attr-defined]
            self.mod._log = lambda *a, **k: None                     # type: ignore[attr-defined]

            real_input = builtins.input
            builtins.input = self.mod.input
            try:
                self.mod.panel_device_manager()
            finally:
                builtins.input = real_input

            saved = json.loads(tmp_registry.read_text())
            self.assertEqual(len(saved["devices"]), 1)
            entry = saved["devices"][0]
            self.assertEqual(entry["status"], "UNVERIFIED")
            self.assertFalse(entry["operator_reviewed"])
            self.assertIsNone(entry["probe_result"])


class TestNoVerdictGenerationOrAuthorityWrites(unittest.TestCase):
    """Static source proofs: the new panels only ever read/display, never
    fabricate verdicts or touch CRAM/PSEUDO authority paths."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def _source(self, fn_name):
        return inspect.getsource(getattr(self.mod, fn_name))

    def test_device_manager_contains_no_verdict_literals(self):
        src = self._source("panel_device_manager")
        self.assertNotIn('"PASS"', src)
        self.assertNotIn('"DROP"', src)

    def test_test_breakdown_contains_no_verdict_literals(self):
        src = self._source("panel_test_breakdown")
        self.assertNotIn('"PASS"', src)
        self.assertNotIn('"DROP"', src)
        # the only verdict-shaped fields it may show must come from artifact data
        self.assertIn("data[key]", src)

    def test_device_manager_never_touches_cram_paths(self):
        src = self._source("panel_device_manager") + self._source("_device_registry_save")
        for forbidden in ("CRAM", "cram_store", "cram_a", "cram_r", "PSEUDO"):
            self.assertNotIn(forbidden, src)

    def test_test_breakdown_is_read_only(self):
        src = self._source("panel_test_breakdown") + self._source("_registered_tests")
        for forbidden in ("write_text", "json.dump", "open(", "_run(", "subprocess"):
            self.assertNotIn(forbidden, src)
        for forbidden in ("CRAM", "cram_store", "cram_a", "cram_r"):
            self.assertNotIn(forbidden, src)


class TestPrototypeNoticeAndFooterConformance(unittest.TestCase):
    """Patch 1.1 — runtime must render the v1.2 doctrine's required
    PH6 Prototype Notice (Section 3) and Permanent Footer (Section 10)
    so the operator is reminded of the workstation hierarchy on screen,
    not only in the doctrine document."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def _source(self, fn_name):
        return inspect.getsource(getattr(self.mod, fn_name))

    def test_notice_helper_contains_required_text(self):
        src = self._source("_prototype_notice")
        self.assertIn("PH6 Prototype Notice", src)
        self.assertIn("Cloud / Claude Terminal", src)
        self.assertIn("SSH Terminal", src)
        self.assertIn("Desktop functions are limited to approved prototype capabilities.", src)

    def test_footer_helper_contains_required_text(self):
        src = self._source("_prototype_footer")
        self.assertIn("Experimental Development Platform", src)
        self.assertIn("Authority:", src)
        self.assertIn("ZERO", src)
        self.assertIn("Lane Impact:", src)
        self.assertIn("None", src)
        self.assertIn("Current Maturity:", src)
        self.assertIn("Early Operational Prototype", src)

    def test_footer_is_rendered_through_shared_header_path(self):
        header_src = self._source("_header")
        self.assertIn("_prototype_footer()", header_src)

    def test_notice_is_rendered_at_startup(self):
        main_src = self._source("main")
        self.assertIn("_prototype_notice()", main_src)


class TestEvidenceReviewCenterClassification(unittest.TestCase):
    """Patch 1.2 — artifact classification must be deterministic and must
    map known PH6 vocabulary (cram/pseudo/soso/...) and media extensions
    to the documented class set."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def _cls(self, name):
        return self.mod._classify_evidence_artifact(Path(f"/tmp/{name}"))

    def test_classifies_known_artifact_names_and_extensions(self):
        cases = {
            "campaign_video_001.mp4":              "VIDEO",
            "frame_000123.jpg":                    "IMAGE",
            "cram_a_manifest.json":                "CRAM",
            "pseudo_a_result.json":                "PSEUDO",
            "soso_advisory_output.json":           "SOSO",
            "rt_token_bundle.json":                "TOKEN",
            "governance_drift_scan_report.json":   "GOVERNANCE",
            "esp_s1_topology.json":                "TOPOLOGY",
            "audit_replay_report.json":            "REPLAY",
            "bme280_sensor_log.json":              "SENSOR",
            "runtime.log":                         "LOG",
            "PH6_FINAL_REPORT.md":                 "REPORT",
            "mystery_blob.dat":                    "UNKNOWN",
        }
        for name, expected in cases.items():
            self.assertEqual(self._cls(name), expected, f"{name} -> expected {expected}")


class TestEvidenceReviewCenterReadOnlyBoundaries(unittest.TestCase):
    """Patch 1.2 — Evidence Review Center must stay strictly read-only over
    CRAM/PSEUDO/SoSo evidence: no writes to reviewed files, no verdict
    fabrication, no authority-path mutation."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def _source(self, fn_name):
        return inspect.getsource(getattr(self.mod, fn_name))

    def test_panel_and_helpers_contain_no_write_modes(self):
        src = (self._source("panel_evidence_review")
               + self._source("_preview_evidence_artifact")
               + self._source("_collect_evidence_artifacts"))
        for forbidden in ("write_text", "write_bytes", "json.dump", "'w'", '"w"', "open(", "_run(", "subprocess"):
            self.assertNotIn(forbidden, src)

    def test_panel_contains_no_verdict_literals(self):
        src = self._source("panel_evidence_review") + self._source("_preview_evidence_artifact")
        self.assertNotIn('"PASS"', src)
        self.assertNotIn('"DROP"', src)

    def test_panel_never_targets_authority_mutation_paths(self):
        src = (self._source("panel_evidence_review")
               + self._source("_preview_evidence_artifact")
               + self._source("_collect_evidence_artifacts"))
        for forbidden in ("cram_store", "pseudo_threshold", "EvidencePacket"):
            self.assertNotIn(forbidden, src)


class TestEvidenceReviewCenterArtifactHandling(unittest.TestCase):
    """Patch 1.2 — artifact collection must parse JSON safely and must
    never crash when configured search roots are missing."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def test_parses_json_artifact_safely(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "pseudo_a_result.json"
            p.write_text(json.dumps({"verdict": "PASS", "test_id": "internal_000001"}))
            entry = {"path": p, "size": p.stat().st_size, "mtime": p.stat().st_mtime,
                     "class": self.mod._classify_evidence_artifact(p)}
            # Must not raise, and must not write to the artifact under review.
            before = p.read_text()
            self.mod._preview_evidence_artifact(entry)
            self.assertEqual(p.read_text(), before)

    def test_collect_handles_missing_roots_without_crashing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            fake_roots = (
                Path(td) / "does_not_exist_1",
                Path(td) / "does_not_exist_2" / "nested",
            )
            self.mod._EVIDENCE_SEARCH_ROOTS = fake_roots
            result = self.mod._collect_evidence_artifacts()
            self.assertEqual(result, [])


class TestEvidencePlaybackAndBreakdown(unittest.TestCase):
    """Patch 1.3 — playback hints, per-class breakdown rendering, and
    test-run timeline grouping must stay strictly read-only and must
    never fabricate or mutate authority data."""

    def setUp(self):
        self.mod = _load_terminal_module()

    def _cls(self, name):
        return self.mod._classify_evidence_artifact(Path(f"/tmp/{name}"))

    def test_video_files_classify_as_video(self):
        for name in ("clip.mp4", "clip.avi", "clip.mkv", "clip.mov", "clip.webm"):
            self.assertEqual(self._cls(name), "VIDEO", name)

    def test_image_files_classify_as_image(self):
        for name in ("frame.jpg", "frame.jpeg", "frame.png", "frame.bmp", "frame.webp"):
            self.assertEqual(self._cls(name), "IMAGE", name)

    def test_cram_files_classify_as_cram(self):
        for name in ("cram_a_object_0001.json", "EvidencePacket_0042.json", "replay_manifest_cram_r.json"):
            self.assertEqual(self._cls(name), "CRAM", name)

    def test_pseudo_files_classify_as_pseudo(self):
        self.assertEqual(self._cls("pseudo_a_verdict.json"), "PSEUDO")

    def test_soso_files_classify_as_soso(self):
        self.assertEqual(self._cls("soso_continuity_graph.json"), "SOSO")

    def test_token_files_classify_as_token(self):
        for name in ("rt_token_0009.json", "vdt_bundle.json", "vlt_decay.json"):
            self.assertEqual(self._cls(name), "TOKEN", name)

    def test_playback_hint_is_display_only_no_execution(self):
        src = inspect.getsource(self.mod._playback_hint)
        for forbidden in ("subprocess", "_run(", "os.system", "os.popen", "Popen"):
            self.assertNotIn(forbidden, src)
        hint = self.mod._playback_hint(Path("/tmp/clip.mp4"))
        self.assertIsInstance(hint, str)
        self.assertIn("clip.mp4", hint)

    def test_missing_playback_tool_does_not_crash(self):
        try:
            hint = self.mod._playback_hint(Path("/tmp/does_not_exist.mkv"))
        except Exception as e:
            self.fail(f"_playback_hint raised: {e}")
        self.assertIsInstance(hint, str)
        self.assertTrue(hint)

    def test_class_breakdown_renders_known_fields_with_required_labels(self):
        import contextlib
        import io
        cases = {
            "SENSOR": {"timestamp": "2026-06-07T00:00:00Z", "device_id": "esp_s1", "sensor_type": "bme280"},
            "CRAM":   {"cram_tier": "CRAM-A", "object_id": "obj_0001"},
            "PSEUDO": {"motion_fraction": 0.12, "entropy": 4.2},
            "SOSO":   {"continuity_id": "cont_0001", "advisory_status": "ADVISORY"},
            "TOKEN":  {"token_id": "rt_0001", "token_type": "RT", "authority": "ZERO"},
        }
        for klass, data in cases.items():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.mod._render_class_breakdown(klass, data)
            out = buf.getvalue()
            self.assertTrue(out.strip(), f"{klass} breakdown produced no output")
            if klass == "SOSO":
                self.assertIn("ADVISORY ONLY", out)
                self.assertIn("AUTHORITY ZERO", out)
            if klass == "TOKEN":
                self.assertIn("MRAM-S ONLY", out)
                self.assertIn("AUTHORITY ZERO", out)

    def test_breakdown_helpers_contain_no_write_modes_or_verdict_generation(self):
        src = (inspect.getsource(self.mod._render_class_breakdown)
               + inspect.getsource(self.mod._playback_hint)
               + inspect.getsource(self.mod._group_evidence_by_test)
               + inspect.getsource(self.mod._render_evidence_test_timeline))
        for forbidden in ("write_text", "write_bytes", "json.dump", "'w'", '"w"', "subprocess", "_run("):
            self.assertNotIn(forbidden, src)
        self.assertNotIn('"PASS"', src)
        self.assertNotIn('"DROP"', src)

    def test_group_by_test_handles_missing_and_ungrouped_paths_safely(self):
        artifacts = [
            {"path": Path("/tmp/PH6_SOURCE/TESTS/20260603_055215/report.json"),
             "size": 10, "mtime": 100.0, "class": "REPORT"},
            {"path": Path("/tmp/loose_file_with_no_test_dir.json"),
             "size": 5, "mtime": 200.0, "class": "UNKNOWN"},
        ]
        groups = self.mod._group_evidence_by_test(artifacts)
        self.assertEqual(len(groups), 2)
        ids = {g["test_id"] for g in groups}
        self.assertIn("20260603_055215", ids)
        # newest-first ordering by last_mtime
        self.assertEqual(groups[0]["last_mtime"], 200.0)


if __name__ == "__main__":
    unittest.main()
