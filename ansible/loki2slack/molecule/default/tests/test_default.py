"""Role testing files using testinfra."""


def test_service(host):
    service = host.service("loki2slack.service")
    assert service.is_enabled
    assert service.is_running

