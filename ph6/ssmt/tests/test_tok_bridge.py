from ph6.ssmt.token_bridge import TokenBridge


def test_tok_bridge_is_not_writable():
    bridge = TokenBridge()
    assert bridge.is_writable() is False


def test_tok_bridge_returns_not_found_for_missing_ref():
    bridge = TokenBridge()
    result = bridge.read_token("tok://rt/nonexistent_ref")
    assert result["status"] == "not_found"


def test_tok_bridge_read_only_contract():
    bridge = TokenBridge()
    assert not hasattr(bridge, "write")
    assert not hasattr(bridge, "delete")
