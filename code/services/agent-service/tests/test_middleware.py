from agent_service.middleware import normalize_request_id


def test_safe_request_id_is_kept() -> None:
    assert normalize_request_id("core-request_123") == "core-request_123"


def test_unsafe_request_id_is_replaced() -> None:
    assert normalize_request_id("unsafe request\nvalue") != "unsafe request\nvalue"
