# PH6 Full Alignment Audit Report

Generated: `2026-05-18T09:32:22.158438Z`

## Executive Verdict

- **DOCTRINE_ALIGNED**: `PASS` ✓
- **GOVERNANCE_ALIGNED**: `PASS` ✓
- **ARCHITECTURE_ALIGNED**: `PASS` ✓
- **TEST_ALIGNED**: `PASS` ✓
- **FUNCTIONALLY_COHERENT**: `PASS` ✓
- **PRODUCTION_CLEARANCE_DECLARED**: `FALSE` ✓
- **GOVERNANCE_DRIFT_SCAN**: `PASS` ✓
- **OVERALL**: `WARN` ⚠

## Summary

- `total_files_scanned`: `629622`
- `py_files_scanned`: `12188`
- `tests_discovered`: `746`
- `finding_count`: `49`
- `fail_count`: `0`
- `warn_count`: `16`
- `critical_count`: `0`
- `high_count`: `10`

## Findings

### [INFO] GOV_governance_manifest.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/governance_manifest.json`
- required governance file present and valid JSON

### [INFO] GOV_forbidden_terms_registry.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/forbidden_terms_registry.json`
- required governance file present and valid JSON

### [INFO] GOV_schema_lock_registry.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/schema_lock_registry.json`
- required governance file present and valid JSON

### [INFO] GOV_severity_policy.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/severity_policy.json`
- required governance file present and valid JSON

### [INFO] GOV_closure_status.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- required governance file present and valid JSON

### [INFO] GOV_evidence_campaign_matrix.json ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/evidence_campaign_matrix.json`
- required governance file present and valid JSON

### [INFO] BOOK_BOOK_0 ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book 0 reference found in source tree

### [INFO] BOOK_BOOK_I ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book I reference found in source tree

### [INFO] BOOK_BOOK_II ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book II reference found in source tree

### [INFO] BOOK_BOOK_III ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book III reference found in source tree

### [INFO] BOOK_BOOK_IV ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book IV reference found in source tree

### [INFO] BOOK_BOOK_V ✓
- **Status**: `PASS`
- **Location**: `PH6_SOURCE`
- Book V reference found in source tree

### [WARN] OLD_DOC_DOC0 ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md`
- old doc marker 'DOC0' found in non-DRAFT files: ['/home/jack/PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md', '/home/jack/PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.md']

### [WARN] OLD_DOC_DOC3 ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md`
- old doc marker 'DOC3' found in non-DRAFT files: ['/home/jack/PH6_SOURCE/00_READ_FIRST_AAI_INGEST_INSTRUCTIONS_v2.0.md', '/home/jack/PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.md']

### [INFO] EVC05_CLOSED_JACK_DISLA ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- EVC-05 CLOSED by Jack Disla: True

### [INFO] PRODUCTION_NOT_DECLARED ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- production clearance correctly not declared

### [INFO] PRODUCTION_STATUS_STRICT_FORM ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- production_clearance_status uses strict form CANDIDATE_NOT_DECLARED: True

### [INFO] CAMPAIGN_CLOSURE_FIELDS_C07 ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- C07 closure fields complete

### [INFO] CAMPAIGN_CLOSURE_FIELDS_EVC-05 ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- EVC-05 closure fields complete

### [INFO] CAMPAIGN_CLOSURE_FIELDS_OI-01 ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- OI-01 closure fields complete

### [INFO] CAMPAIGN_CLOSURE_FIELDS_OI-03A ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- OI-03A closure fields complete

### [INFO] CAMPAIGN_CLOSURE_FIELDS_OI-03B ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- OI-03B closure fields complete

### [INFO] CAMPAIGN_CLOSURE_FIELDS_OI-03C ✓
- **Status**: `PASS`
- **Location**: `/home/jack/PH6_SOURCE/GOVERNANCE/closure_status.json`
- OI-03C closure fields complete

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_CLOSEKIT/failure_injection/fi_04_lane2_contamination.py`
- possible forbidden pattern: motion_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_CLOSEKIT/failure_injection/fi_04_lane2_contamination.py`
- possible forbidden pattern: motion_decay_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/PH6_CLOSEKIT/failure_injection/fi_04_lane2_contamination.py`
- possible forbidden pattern: motion_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/PH6_CLOSEKIT/failure_injection/fi_04_lane2_contamination.py`
- possible forbidden pattern: motion_decay_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/oi-env/lib/python3.13/site-packages/interpreter/core/computer/display/point/point.py`
- possible forbidden pattern: adaptive_threshold

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/oi-env/lib/python3.13/site-packages/pygments/lexers/_stan_builtins.py`
- possible forbidden pattern: hidden_state_mutation

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/ph6/cram_pu/tok_soso_isolation_proof.py`
- possible forbidden pattern: motion_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/ph6/cram_pu/tok_soso_isolation_proof.py`
- possible forbidden pattern: motion_decay_score

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/ph6/cram_pu/tools/run_c10_c11_c12_absorption_campaigns.py`
- possible forbidden pattern: adaptive_threshold

### [HIGH] FORBIDDEN_AUTHORITY_PATTERN ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/ph6_cram_lane1_evidence_chain_test.py`
- possible forbidden pattern: motion_score

### [WARN] SHA256_PRIMARY_AUTHORITY ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6lite_v02/cram_writer.py`
- authority-path file uses SHA-256 without BLAKE2b

### [WARN] SHA256_PRIMARY_AUTHORITY ⚠
- **Status**: `WARN`
- **Location**: `/home/jack/ph6lite_v02/cram_writer.py`
- authority-path file uses SHA-256 without BLAKE2b

### [WARN] PSEUDO_A_FILES_PRESENT ⚠
- **Status**: `WARN`
- **Location**: `ph6/`
- PSEUDO-A implementation files found: []

### [INFO] CRAM_ATOMIC_COMMIT_PRESENT ✓
- **Status**: `PASS`
- **Location**: `/home/jack/ph6/cram_pu/tools/cram_pu_atomic_commit.py`
- CRAM atomic commit mechanism present

### [INFO] MRAM_S_NOT_IN_AUTHORITY_COMMIT ✓
- **Status**: `PASS`
- **Location**: `/home/jack/ph6/cram_pu/tools/cram_pu_atomic_commit.py`
- MRAM-S not in authority commit path

### [WARN] TEST_CLASSES_MISSING ⚠
- **Status**: `WARN`
- **Location**: `ph6/tests`
- no tests found for categories: ['deterministic_gate_math', 'governance', 'rsync_nonblocking']

### [INFO] STALE_TEST_SCAN ✓
- **Status**: `PASS`
- **Location**: `ph6/tests`
- no deprecated terms found in test files

### [INFO] PIPELINE_INTAKE___DEPARTURE ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'intake / departure': found

### [INFO] PIPELINE_PSEUDO_MEASUREMENT ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'PSEUDO measurement': found

### [INFO] PIPELINE_PASS_DROP_ADJUDICATION ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'PASS/DROP adjudication': found

### [INFO] PIPELINE_CRAM_COMMIT ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'CRAM commit': found

### [INFO] PIPELINE_AUDIT_EMISSION ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'audit emission': found

### [INFO] PIPELINE_REPLAY_VERIFICATION ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'replay verification': found

### [INFO] PIPELINE_RSYNC___EXPORT ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'RSYNC / export': found

### [INFO] PIPELINE_LANE_2_ISOLATION ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'Lane 2 isolation': found

### [INFO] PIPELINE_GOVERNANCE_SCAN ✓
- **Status**: `PASS`
- **Location**: `ph6/`
- pipeline component 'governance scan': found


## Tests Discovered


### advisory_containment
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/tok/tests/test_tok_boundaries.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/tok/tests/test_stub_imports.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_tok_bridge.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_scheduler.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_hash_chain.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_ssmt_boundaries.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_audit_log.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_failure_injection.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_tokenize.py`
- `ph6/tok/tests/test_tok_boundaries.py`
- `ph6/tok/tests/test_stub_imports.py`
- `ph6/ssmt/tests/test_tok_bridge.py`
- `ph6/ssmt/tests/test_scheduler.py`
- `ph6/ssmt/tests/test_hash_chain.py`
- `ph6/ssmt/tests/test_ssmt_boundaries.py`
- `ph6/ssmt/tests/test_audit_log.py`
- `ph6/ssmt/tests/test_failure_injection.py`
- `ph6/ssmt/tests/test_soso_contract.py`

### cram_write_recovery
- `ph6lite_v02/test_atomic_jetson.py`
- `ph6_cram_sender/send_test_frame.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6lite_v02/test_atomic_jetson.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6_cram_sender/send_test_frame.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/cram_pu/run_4pass_system_test.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/cram_pu/run_two_pi_transfer_test.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/cram_pu/tests/test_closure_patches.py`
- `ph6/cram_pu/run_4pass_system_test.py`
- `ph6/cram_pu/run_two_pi_transfer_test.py`
- `ph6/cram_pu/tests/test_ingest_receipt_chain.py`
- `ph6/cram_pu/tests/test_vrc.py`
- `ph6/cram_pu/tests/test_closure_patches.py`

### lane_isolation
- `ph6_cram_lane1_evidence_chain_test.py`
- `ph6_usb_cram_lane1_soso_test.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_no_authority_leakage.py`
- `ph6/ssmt/tests/test_no_authority_leakage.py`

### replay_parity
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/cram_pu/tests/test_crash_replay.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_replay_receipt.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/ssmt/tests/test_replay_independence.py`
- `ph6/cram_pu/tests/test_crash_replay.py`
- `ph6/ssmt/tests/test_replay_receipt.py`
- `ph6/ssmt/tests/test_replay_independence.py`

### schema
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6/cram_pu/tests/test_canonical_schemas.py`
- `oi-env/lib/python3.13/site-packages/jsonschema_specifications/tests/test_jsonschema_specifications.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_jsonschema_test_suite.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_deprecations.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_utils.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_types.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_validators.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_exceptions.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_format.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/test_cli.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/benchmarks/json_schema_test_suite.py`
- `oi-env/lib/python3.13/site-packages/jsonschema/tests/typing/test_all_concrete_validators_match_protocol.py`
- `oi-env/lib/python3.13/site-packages/referencing/tests/test_jsonschema.py`
- `ph6/cram_pu/tests/test_canonical_schemas.py`

### unclassified
- `test_ph6_stack_inventory.py`
- `ph6lite_v02/test_ph6lite.py`
- `ph6lite_cam/test_m6_mark2.py`
- `ph6lite_cam/ph6_camera_deterministic_test.py`
- `ph6_storage_monitor/test_storage_monitor.py`
- `ph6_smi11_drop/ph6_camera_test_smi11.py`
- `ph6_usb_camera_tests/ph6_extended_stability_test.py`
- `ph6_usb_camera_tests/ph6_usb_300_frame_test.py`
- `ph6_usb_camera_tests/ph6_av_contention_test.py`
- `ph6_usb_camera_tests/usb_camera_quick_test.py`
- `ph6_esp32cam_tests/ph6_esp32cam_300_frame_test.py`
- `.local/lib/python3.13/site-packages/_pytest/doctest.py`
- `.local/lib/python3.13/site-packages/_pytest/subtests.py`
- `.local/lib/python3.13/site-packages/_pytest/pytester_assertions.py`
- `.local/lib/python3.13/site-packages/_pytest/unittest.py`
- `.local/lib/python3.13/site-packages/_pytest/pytester.py`
- `.local/lib/python3.13/site-packages/anyio/pytest_plugin.py`
- `.local/lib/python3.13/site-packages/annotated_types/test_cases.py`
- `.local/lib/python3.13/site-packages/click/testing.py`
- `.local/lib/python3.13/site-packages/starlette/testclient.py`
- `.local/lib/python3.13/site-packages/fastapi/testclient.py`
- `.local/lib/python3.13/site-packages/platformio/remote/client/run_or_test.py`
- `.local/lib/python3.13/site-packages/platformio/test/runners/doctest.py`
- `.local/lib/python3.13/site-packages/platformio/test/runners/googletest.py`
- `.local/lib/python3.13/site-packages/platformio/builder/tools/piotest.py`
- `.local/lib/python3.13/site-packages/colorama/tests/ansitowin32_test.py`
- `.local/lib/python3.13/site-packages/colorama/tests/initialise_test.py`
- `.local/lib/python3.13/site-packages/colorama/tests/isatty_test.py`
- `.local/lib/python3.13/site-packages/colorama/tests/winterm_test.py`
- `.local/lib/python3.13/site-packages/colorama/tests/ansi_test.py`
- `.local/lib/python3.13/site-packages/ajsonrpc/tests/test_core.py`
- `.local/lib/python3.13/site-packages/ajsonrpc/tests/test_manager.py`
- `.local/lib/python3.13/site-packages/ajsonrpc/tests/test_dispatcher.py`
- `.local/lib/python3.13/site-packages/anyio/abc/_testing.py`
- `.local/lib/python3.13/site-packages/anyio/_core/_testing.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/test_ph6_stack_inventory.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6lite_v02/test_ph6lite.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6lite_cam/test_m6_mark2.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6lite_cam/ph6_camera_deterministic_test.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/ph6_storage_monitor/test_storage_monitor.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/_pytest/doctest.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/_pytest/subtests.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/_pytest/pytester_assertions.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/_pytest/unittest.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/_pytest/pytester.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/anyio/pytest_plugin.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/annotated_types/test_cases.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/click/testing.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/starlette/testclient.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/fastapi/testclient.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/anyio/abc/_testing.py`
- `PH6_LOCAL_BACKUPS/PH6_CHECKPOINT_20260513T223257Z/SOURCE_CHECKPOINT/home_jack_source/.local/lib/python3.13/site-packages/anyio/_core/_testing.py`
- `oi-env/lib/python3.13/site-packages/pyparsing/testing.py`
- `oi-env/lib/python3.13/site-packages/anyio/pytest_plugin.py`
- `oi-env/lib/python3.13/site-packages/fsspec/conftest.py`
- `oi-env/lib/python3.13/site-packages/aiohttp/test_utils.py`
- `oi-env/lib/python3.13/site-packages/aiohttp/pytest_plugin.py`
- `oi-env/lib/python3.13/site-packages/annotated_types/test_cases.py`
- `oi-env/lib/python3.13/site-packages/shortuuid/test_shortuuid.py`
- `oi-env/lib/python3.13/site-packages/typer/testing.py`
- `oi-env/lib/python3.13/site-packages/click/testing.py`
- `oi-env/lib/python3.13/site-packages/numpy/conftest.py`
- `oi-env/lib/python3.13/site-packages/numpy/_pytesttester.py`
- `oi-env/lib/python3.13/site-packages/tornado/testing.py`
- `oi-env/lib/python3.13/site-packages/executing/_pytest_utils.py`
- `oi-env/lib/python3.13/site-packages/jinja2/tests.py`
- `oi-env/lib/python3.13/site-packages/starlette/testclient.py`
- `oi-env/lib/python3.13/site-packages/joblib/testing.py`
- `oi-env/lib/python3.13/site-packages/pygments/lexers/testing.py`
- `oi-env/lib/python3.13/site-packages/jedi/plugins/pytest.py`
- `oi-env/lib/python3.13/site-packages/litellm/integrations/test_httpx.py`
- `oi-env/lib/python3.13/site-packages/litellm/proxy/example_config_yaml/pipeline_test_guardrails.py`
- `oi-env/lib/python3.13/site-packages/litellm/proxy/guardrails/guardrail_hooks/litellm_content_filter/guardrail_benchmarks/test_eval.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_testing.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_numpy_pickle_compat.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_logger.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_utils.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_cloudpickle_wrapper.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_numpy_pickle_utils.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_numpy_pickle.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_parallel.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_module.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_disk.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_store_backends.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_memory_async.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/testutils.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_missing_multiprocessing.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_memory.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_hashing.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_memmapping.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_func_inspect.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_init.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_func_inspect_special_encoding.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_backports.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_config.py`
- `oi-env/lib/python3.13/site-packages/joblib/test/test_dask.py`
- `oi-env/lib/python3.13/site-packages/traitlets/tests/test_traitlets.py`
- `oi-env/lib/python3.13/site-packages/smmap/test/test_buf.py`
- `oi-env/lib/python3.13/site-packages/smmap/test/test_tutorial.py`
- `oi-env/lib/python3.13/site-packages/smmap/test/test_mman.py`
- `oi-env/lib/python3.13/site-packages/smmap/test/test_util.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/pydevd_attach_to_process/_test_attach_to_process_linux.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/pydevd_attach_to_process/_test_attach_to_process.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydev_runfiles/pydev_runfiles_pytest2.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydev_runfiles/pydev_runfiles_unittest.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_concrete.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_code.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_instr.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_peephole_opt.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_flags.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_cfg.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_bytecode.py`
- `oi-env/lib/python3.13/site-packages/debugpy/_vendored/pydevd/_pydevd_frame_eval/vendored/bytecode/tests/test_misc.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/gen_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/iostream_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/httpserver_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/autoreload_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/options_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/concurrent_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/wsgi_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/runtests.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/util_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/httputil_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/http1connection_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/circlerefs_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/httpclient_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/process_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/curl_httpclient_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/resolve_test_helper.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/netutil_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/websocket_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/simple_httpclient_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/testing_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/routing_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/queues_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/twisted_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/log_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/web_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/escape_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/ioloop_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/asyncio_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/locks_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/tcpserver_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/auth_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/locale_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/template_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/tcpclient_test.py`
- `oi-env/lib/python3.13/site-packages/tornado/test/import_test.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_pkg_resources.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_find_distributions.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_integration_zope_interface.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_markers.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_resources.py`
- `oi-env/lib/python3.13/site-packages/pkg_resources/tests/test_working_set.py`
- `oi-env/lib/python3.13/site-packages/gitdb/test/test_example.py`
- `oi-env/lib/python3.13/site-packages/gitdb/test/test_stream.py`
- `oi-env/lib/python3.13/site-packages/gitdb/test/test_pack.py`
- `oi-env/lib/python3.13/site-packages/gitdb/test/test_base.py`
- `oi-env/lib/python3.13/site-packages/gitdb/test/test_util.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_http.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_utils.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_ssl_edge_cases.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_abnf.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_cookiejar.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_app.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_ssl_compat.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_large_payloads.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_url.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_websocket.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_dispatcher.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_socket_bugs.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_handshake_large_response.py`
- `oi-env/lib/python3.13/site-packages/websocket/tests/test_socket.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_lazyloading.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test__all__.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_scripts.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_reloading.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_warnings.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_public_api.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_configtool.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_ctypeslib.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_numpy_version.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_matlib.py`
- `oi-env/lib/python3.13/site-packages/numpy/tests/test_numpy_config.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/testutils.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_return_character.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_assumed_shape.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_character.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_string.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_routines.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_pyf_src.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_f2cmap.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_docs.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_f2py2e.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_symbolic.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_return_complex.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_value_attrspec.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_array_from_pyobj.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_kind.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_return_logical.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_size.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_abstract_interface.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_mixed.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_semicolon_split.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_data.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_block_docstring.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_common.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_quoted_character.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_return_integer.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_return_real.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_callback.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_parameter.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_isoc.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_crackfortran.py`
- `oi-env/lib/python3.13/site-packages/numpy/f2py/tests/test_modules.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_numerictypes.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_nditer.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalarprint.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_argparse.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_datetime.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_umath_accuracy.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_memmap.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_half.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_deprecations.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_arraymethod.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_extint128.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalar_ctors.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalarbuffer.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_errstate.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_indexing.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_mem_policy.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_umath.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_array_coercion.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_hashtable.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_strings.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_umath_complex.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_stringdtype.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_cython.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_numeric.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_item_selection.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalarinherit.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_multithreading.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_conversion_utils.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_defchararray.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_array_interface.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_finfo.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_api.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_einsum.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_simd.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_dlpack.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_function_base.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_records.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_simd_module.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_custom_dtypes.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_multiprocessing.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_dtype.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_cpu_dispatcher.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_nep50_promotions.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_abc.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalarmath.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_arrayprint.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_casting_unittests.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_arrayobject.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_cpu_features.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_longdouble.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_array_api_info.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test__exceptions.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_protocols.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_casting_floatingpoint_errors.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_mem_overlap.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_overrides.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_indexerrors.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_unicode.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_multiarray.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_getlimits.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_scalar_methods.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_ufunc.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_shape_base.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_limited_api.py`
- `oi-env/lib/python3.13/site-packages/numpy/_core/tests/test_print.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_core.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_deprecations.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_subclassing.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_extras.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_arrayobject.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_mrecords.py`
- `oi-env/lib/python3.13/site-packages/numpy/ma/tests/test_old_ma.py`
- `oi-env/lib/python3.13/site-packages/numpy/fft/tests/test_helper.py`
- `oi-env/lib/python3.13/site-packages/numpy/fft/tests/test_pocketfft.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_direct.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_generator_mt19937.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_extending.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_randomstate.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_random.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_generator_mt19937_regressions.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_smoke.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_seed_sequence.py`
- `oi-env/lib/python3.13/site-packages/numpy/random/tests/test_randomstate_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_type_check.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_histograms.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_stride_tricks.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_arraypad.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_mixins.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_twodim_base.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_utils.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_array_utils.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test__iotools.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_nanfunctions.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_function_base.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test__version.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_packbits.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test__datasource.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_arrayterator.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_io.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_loadtxt.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_recfunctions.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_format.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_index_tricks.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_polynomial.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_shape_base.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_ufunclike.py`
- `oi-env/lib/python3.13/site-packages/numpy/lib/tests/test_arraysetops.py`
- `oi-env/lib/python3.13/site-packages/numpy/linalg/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/linalg/tests/test_deprecations.py`
- `oi-env/lib/python3.13/site-packages/numpy/linalg/tests/test_linalg.py`
- `oi-env/lib/python3.13/site-packages/numpy/typing/tests/test_runtime.py`
- `oi-env/lib/python3.13/site-packages/numpy/typing/tests/test_typing.py`
- `oi-env/lib/python3.13/site-packages/numpy/typing/tests/test_isfile.py`
- `oi-env/lib/python3.13/site-packages/numpy/testing/tests/test_utils.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_laguerre.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_classes.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_symbol.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_hermite_e.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_hermite.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_polyutils.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_legendre.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_printing.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_polynomial.py`
- `oi-env/lib/python3.13/site-packages/numpy/polynomial/tests/test_chebyshev.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_regression.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_defmatrix.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_numeric.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_masked_matrix.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_matrix_linalg.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_multiarray.py`
- `oi-env/lib/python3.13/site-packages/numpy/matrixlib/tests/test_interaction.py`
- `oi-env/lib/python3.13/site-packages/numpy/_pyinstaller/tests/test_pyinstaller.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_repl.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_tracing.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_unix_pipes.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_dtls.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_windows_pipes.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_testing.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_scheduler_determinism.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_file_io.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_ssl.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_open_tcp_listeners.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_subprocess.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/pytest_plugin.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_path.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_threads.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_deprecate_strict_exception_groups_false.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_contextvars.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_serve_listeners.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_open_unix_stream.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_sync.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_deprecate.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_ssl_helpers.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_abc.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_testing_raisesgroup.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_channel.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_generic.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_fakenet.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_signals.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_wait_for_object.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_open_tcp_stream.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_timeouts.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_highlevel_socket.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_socket.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_exports.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_util.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/test_trio.py`
- `oi-env/lib/python3.13/site-packages/trio/testing/_trio_test.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_guest_mode.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_ki.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_instrumentation.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_unbounded_queue.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_mock_clock.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_tutil.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_local.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_asyncgen.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_exceptiongroup_gc.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_parking_lot.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_cancelled.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_thread_cache.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_io.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_run.py`
- `oi-env/lib/python3.13/site-packages/trio/_core/_tests/test_windows.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/tools/test_mypy_annotate.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/tools/test_gen_exports.py`
- `oi-env/lib/python3.13/site-packages/trio/_tests/tools/test_sync_requirements.py`
- `oi-env/lib/python3.13/site-packages/fontTools/misc/testTools.py`
- `oi-env/lib/python3.13/site-packages/fontTools/varLib/interpolatableTestContourOrder.py`
- `oi-env/lib/python3.13/site-packages/fontTools/varLib/interpolatableTestStartingPoint.py`
- `oi-env/lib/python3.13/site-packages/setuptools/command/test.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_extern.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_build_meta.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_shutil_wrapper.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_scripts.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_setopt.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_find_py_modules.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_build.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_find_packages.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_depends.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_warnings.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_build_ext.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_logging.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_archive_util.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_config_discovery.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_egg_info.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_distutils_adoption.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_dist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_bdist_wheel.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_manifest.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_install_scripts.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_build_clib.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_dist_info.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_bdist_deprecations.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_build_py.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_windows_wrappers.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_core_metadata.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_sdist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_wheel.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_setuptools.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_virtualenv.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_glob.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_bdist_egg.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_namespaces.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_unicode_utils.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_editable_install.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/test_develop.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_install.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_log.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_build.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_core.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_build_ext.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_extension.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_install_data.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_filelist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_dir_util.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_archive_util.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_text_file.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_install_lib.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_modified.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_install_headers.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_dist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_version.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_install_scripts.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_bdist_dumb.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_sysconfig.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_build_scripts.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_config_cmd.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_bdist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_spawn.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_build_clib.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_clean.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_build_py.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_sdist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_versionpredicate.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_bdist_rpm.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_cmd.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_util.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_file_util.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/tests/test_check.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/compilers/C/tests/test_base.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/compilers/C/tests/test_mingw.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/compilers/C/tests/test_unix.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/compilers/C/tests/test_cygwin.py`
- `oi-env/lib/python3.13/site-packages/setuptools/_distutils/compilers/C/tests/test_msvc.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/integration/test_pbr.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/integration/test_pip_install_sdist.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/config/test_apply_pyprojecttoml.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/config/test_expand.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/config/test_setupcfg.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/config/test_pyprojecttoml_dynamic_deps.py`
- `oi-env/lib/python3.13/site-packages/setuptools/tests/config/test_pyprojecttoml.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_memleaks.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_osx.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_contracts.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_bsd.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_aix.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_process_all.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_process.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_posix.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_testutils.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_sunos.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_system.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_unicode.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_connections.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_windows.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_linux.py`
- `oi-env/lib/python3.13/site-packages/psutil/tests/test_misc.py`
- `oi-env/lib/python3.13/site-packages/anyio/abc/_testing.py`
- `oi-env/lib/python3.13/site-packages/anyio/_core/_testing.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/conftest.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/test_filestring_sandbox.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_corpus_views.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_chunk.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_bllip.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_twitter_auth.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_nombank.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_downloader_unzip.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_corpora.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_verbnet.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_segmentation.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_tag.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_corenlp.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_aline.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_pos_tag.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_texttiling.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_pickle_load_warnings.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_wordnet.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_disagreement.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_rte_classify.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_pathsec.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_brill.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_freqdist.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_ribes.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_distance.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_stem.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_senna.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_naivebayes.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_corpus_reader.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_data_security.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_pl196x.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_cfg2chomsky.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_open_datafile.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_data.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_downloader.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_corpus_util.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_seekable_unicode_stream_reader.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_json_serialization.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_metrics.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_concordance.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_cfd_mutation.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_json2csv_corpus.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_tgrep.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_classify.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_collocations.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_util.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/test_hmm.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm2.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_meteor.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm3.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_gdfa.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm1.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_nist.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm5.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm4.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_bleu.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_ibm_model.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/translate/test_stack_decoder.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/lm/test_vocabulary.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/lm/test_preprocessing.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/lm/test_counter.py`
- `oi-env/lib/python3.13/site-packages/nltk/test/unit/lm/test_models.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/mplot3d/tests/conftest.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/mplot3d/tests/test_axes3d.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/mplot3d/tests/test_art3d.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/mplot3d/tests/test_legend3d.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_axislines.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_grid_helper_curvelinear.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/conftest.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_floating_axes.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_grid_finder.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_angle_helper.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axisartist/tests/test_axis_artist.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axes_grid1/tests/conftest.py`
- `oi-env/lib/python3.13/site-packages/mpl_toolkits/axes_grid1/tests/test_axes_grid1.py`
- `oi-env/lib/python3.13/site-packages/referencing/tests/test_core.py`
- `oi-env/lib/python3.13/site-packages/referencing/tests/test_referencing_suite.py`
- `oi-env/lib/python3.13/site-packages/referencing/tests/test_retrieval.py`
- `oi-env/lib/python3.13/site-packages/referencing/tests/test_exceptions.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/testing/conftest.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_offsetbox.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_ticker.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_afm.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_type1font.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_cycles.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_gridspec.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_svg.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_polar.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_subplots.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_datetime.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/conftest.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_tightlayout.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_dviread.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_bases.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_determinism.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_triangulation.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_multivariate_colormaps.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_testing.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_font_manager.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_table.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_textpath.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_doc.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_container.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_cbook.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_matplotlib.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_path.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_bbox_tight.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backends_interactive.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_axis.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_cairo.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_pgf.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_contour.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_macosx.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_inline.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_constrainedlayout.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_style.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_qt.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_nbagg.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_usetex.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_basic.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_colors.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_webagg.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_scale.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_dates.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_image.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_spines.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_pyplot.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_pickle.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_pdf.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_api.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_quiver.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_png.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_tk.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_artist.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_mathtext.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_getattr.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_transforms.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_colorbar.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_marker.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_rcparams.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_streamplot.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_ft2font.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_fontconfig_pattern.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_widgets.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_legend.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_compare_images.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_agg.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_patheffects.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_arrow_patches.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_mlab.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_template.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_units.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_collections.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_bezier.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_category.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_gtk3.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_skew.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_text.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_animation.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_tools.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_texmanager.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_preprocess_data.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_lines.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_sphinxext.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_registry.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_figure.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_axes.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_backend_ps.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_simplification.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_patches.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_sankey.py`
- `oi-env/lib/python3.13/site-packages/matplotlib/tests/test_agg_filter.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/skipdoctest.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/ipunittest.py`
- `oi-env/lib/python3.13/site-packages/IPython/sphinxext/custom_doctests.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/plugin/pytest_ipdoctest.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/plugin/ipdoctest.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/plugin/test_refs.py`
- `oi-env/lib/python3.13/site-packages/IPython/testing/plugin/test_ipdoctest.py`
- `oi-env/lib/python3.13/site-packages/regex/tests/test_regex.py`
- `oi-env/lib/python3.13/site-packages/sniffio/_tests/test_sniffio.py`
- `oi-env/lib/python3.13/site-packages/google/generativeai/notebook/post_process_utils_test_helper.py`
- `oi-env/lib/python3.13/site-packages/google/protobuf/internal/testing_refleaks.py`

## Governance Tool Outputs

### `git log --oneline -n 10`
- Return code: `0`
```
37c62a2fff governance: tighten EVC-05 closure status; production remains undeclared
46aba55168 governance: Jack Disla — EVC-05 closed; production clearance candidate (hardened patch)
f19d32ddd5 evidence: EVC-05 review closure pending authority signature
579ae14a42 governance: Jack Disla — EVC-05 closed; production clearance candidate
9deda5b1ab evidence: EVC-05 production-grade phased Life CRAM campaign PASS_PENDING_REVIEW
a26c111c25 governance: Jack Disla review closure — C07, OI-03A/B/C closed; OI-01 descoped
3a6049e128 governance: record OI-03A/B/C cross-node transfer proof evidence levels
2e42ce3705 evidence: OI-03C 3600-frame cross-node transfer proof PASS_PENDING_REVIEW
e445e7a3be evidence: OI-03B 1200-frame cross-node transfer proof PASS_PENDING_REVIEW
1c1a430e47 evidence: OI-03A mini real-evidence cross-node transfer proof PASS_PENDING_REVIEW

```
### `git status --short`
- Return code: `0`
```

?? PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.json
?? PH6_SOURCE/GOVERNANCE/ph6_full_alignment_audit_report.md
?? PH6_SOURCE/TOOLS/ph6_full_alignment_audit.py
?? PH6_SOURCE/builds/
?? apply_closure_patch.py
?? apply_evc05_closure.py
?? cram_pu_live_1_0/runtime/
?? esp32cam_fw/
?? esp32cam_ingest_300.py
?? esp32cam_test.jpg
?? ph6/audit.py
?? ph6/cram_pu/evc04_live_payload_replay.py
?? ph6/cram_pu/run_evc02.sh
?? ph6/cram_pu/run_evc04_live_replay.sh
?? ph6/cram_pu/run_evc04_replay.sh
?? ph6/cram_pu/runtime/oi03_phase1_20260516T084449Z/
?? ph6/cram_pu/runtime/oi03_phase2_20260516T084619Z/
?? ph6/cram_pu/runtime/oi03_phase3_20260516T084757Z/
?? ph6/cram_pu/runtime/run_20260506T102907Z/
?? ph6/cram_pu/runtime/run_20260506T103247Z/
?? ph6/cram_pu/runtime/run_20260515T100522Z/
?? ph6/cram_pu/runtime/run_20260516T083606Z/
?? ph6/cram_pu/runtime/run_20260516T083740Z/
?? ph6/cram_pu/runtime/run_20260516T214325Z/
?? ph6/cram_pu/runtime/run_20260516T215224Z/
?? ph6/cram_pu/runtime/tok_leak_001_20260516T083748Z_tok_off/
?? ph6/cram_pu/runtime/tok_leak_001_20260516T083748Z_tok_on/
?? ph6/cram_pu/runtime/two_pi_20260506T111235Z/
?? ph6/cram_pu/validation_runs/20260506T111731Z/
?? ph6/cram_pu/validation_runs/evc02_20260516T214858Z/
?? ph6/cram_pu/validation_runs/evc02_20260516T214907Z/
?? ph6/cram_pu/validation_runs/evc04_20260516T212620Z/
?? ph6/cram_pu/validation_runs/evc04_20260516T213359Z/
?? ph6/cram_pu/validation_runs/evc04_20260516T213410Z/
?? ph6/cram_pu/validation_runs/evc04_20260516T214340Z/
?? ph6/cram_pu/validation_runs/evc04_20260516T214915Z/
?? ph6/cram_pu/validation_runs/lcc01_C_20260518T071209Z/
?? ph6/cram_pu/validation_runs/lcc01_smoke_test/
?? ph6/cram_pu/validation_runs/lcc01_smoke_test_20260518T070047Z/
?? ph6/validation_runs/
?? ph6_console.py
?? ph6_esp32cam_tests/
?? ph6_esp32cam_validation/
?? ph6_iphone_ingest/
?? ph6_smi11_drop/
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0000.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0030.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0060.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0090.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0120.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0150.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/chunk_0179.wav
?? ph6_usb_camera_tests/audio_test_20260515T095839Z/raw_capture.wav
?? ph6_usb_camera_tests/av_contention_20260515T100154Z/
?? ph6_usb_camera_tests/av_contention_20260515T100841Z/audio_capture.wav
?? ph6_usb_camera_tests/gap16_r2_20260515T101657Z/audio_capture.wav
?? ph6_usb_camera_tests/gap16b_isolation_20260515T102608Z/
?? ph6_usb_camera_tests/ph6_extended_stability_test.py
?? ph6_usb_camera_tests/ph6_gap16b_isolation.py
?? ph6_usb_camera_tests/usb_test_20260514T225126Z/
?? ph6_usb_camera_tests/usb_test_20260514T225142Z/
?? ph6_usb_camera_tests/usb_test_20260514T225157Z/
?? ph6_video_tests/
?? usb3_nvme_calibration/
?? validation_runs/

```
### `python3 /home/jack/PH6_SOURCE/TOOLS/governance_drift_scan.py --scan-root PH6_SOU`
- Return code: `0`
```

PH6 GOVERNANCE DRIFT SCAN
  scan_root:   /home/jack/PH6_SOURCE
  generated:   2026-05-18T09:32:19Z
  result:      PASS
  critical:    0
  high:        0
  warn:        0



```
### `python3 /home/jack/PH6_SOURCE/TOOLS/ai_preflight_check.py --root . --json-out PH`
- Return code: `2`
### `python3 -m pytest /home/jack/ph6/cram_pu/tests -v --tb=short --no-header -q`
- Return code: `0`
```
============================= test session starts ==============================
collected 114 items

ph6/cram_pu/tests/test_canonical_schemas.py ............................ [ 24%]
...                                                                      [ 27%]
ph6/cram_pu/tests/test_closure_patches.py ..................             [ 42%]
ph6/cram_pu/tests/test_crash_replay.py ................................. [ 71%]
....                                                                     [ 75%]
ph6/cram_pu/tests/test_ingest_receipt_chain.py ..........                [ 84%]
ph6/cram_pu/tests/test_vrc.py ..................                         [100%]

============================= 114 passed in 1.04s ==============================

```
### `python3 -m pytest /home/jack/ph6/ssmt/tests -v --tb=short --no-header -q`
- Return code: `0`
```
============================= test session starts ==============================
collected 52 items

ph6/ssmt/tests/test_audit_log.py .....                                   [  9%]
ph6/ssmt/tests/test_failure_injection.py .............                   [ 34%]
ph6/ssmt/tests/test_hash_chain.py ........                               [ 50%]
ph6/ssmt/tests/test_no_authority_leakage.py ..                           [ 53%]
ph6/ssmt/tests/test_replay_independence.py .                             [ 55%]
ph6/ssmt/tests/test_replay_receipt.py .....                              [ 65%]
ph6/ssmt/tests/test_scheduler.py ...                                     [ 71%]
ph6/ssmt/tests/test_soso_contract.py .........                           [ 88%]
ph6/ssmt/tests/test_ssmt_boundaries.py ...                               [ 94%]
ph6/ssmt/tests/test_tok_bridge.py ...                                    [100%]

============================== 52 passed in 0.10s ==============================

```
### `python3 -m pytest /home/jack/ph6/tok/tests -v --tb=short --no-header -q`
- Return code: `0`
```
============================= test session starts ==============================
collected 12 items

ph6/tok/tests/test_stub_imports.py .........                             [ 75%]
ph6/tok/tests/test_tok_boundaries.py ...                                 [100%]

============================== 12 passed in 0.04s ==============================

```
