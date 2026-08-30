from agent_service.logging_config import mask_sensitive_text


def test_sensitive_values_are_masked() -> None:
    message = "password=demo token:abc api_key=key123 action=health"

    assert mask_sensitive_text(message) == ("password=*** token:*** api_key=*** action=health")
