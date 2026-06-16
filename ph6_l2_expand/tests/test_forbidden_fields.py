from ph6_l2_expand.boundary_guard import classify, scan


def test_clean_payload_is_ok():
    payload = {
        "schema": "ph6_mram_s_advisory_v1",
        "observations": ["observed field 'motion_fraction'"],
        "advisory_data": {"stable_link_count": 2, "topology_density": "0.5000"},
    }
    status, violations = classify(payload)
    assert status == "OK"
    assert violations == []


def test_verdict_field_is_forbidden():
    status, violations = classify({"verdict": "interesting"})
    assert status == "DRIFT_FAIL"
    assert violations


def test_pass_drop_words_are_forbidden():
    for word in ("PASS", "DROP", "ACCEPT", "REJECT", "PROMOTE"):
        status, _ = classify({"note": f"the system should {word} this object"})
        assert status == "DRIFT_FAIL", word


def test_threshold_and_evidence_packet_are_forbidden():
    assert classify({"note": "adjust the threshold"})[0] == "DRIFT_FAIL"
    assert classify({"note": "this references EvidencePacket"})[0] == "DRIFT_FAIL"


def test_lane1_modification_phrases_are_forbidden():
    for phrase in ("modify CRAM", "modify PSEUDO", "modify replay", "modify gate"):
        status, _ = classify({"note": f"do not {phrase} ever"})
        assert status == "DRIFT_FAIL", phrase


def test_word_boundary_does_not_false_positive():
    # "promoted_from" / "password" must not trigger PROMOTE / PASS as substrings
    status, violations = classify({"promoted_from": "abc123", "field": "password_hint"})
    assert status == "OK", violations


def test_scan_returns_path_information():
    violations = scan({"a": {"b": ["PASS"]}})
    assert violations
    assert "a.b[0]" in violations[0]
