from datetime import timedelta
from types import SimpleNamespace

from sales_genie.client import GenieClient


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def as_dict(self):
        return self.payload


class _FakeGenie:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return _Response({"called": name})

        return record


def _client():
    client = object.__new__(GenieClient)
    genie = _FakeGenie()
    client.workspace = SimpleNamespace(genie=genie)
    return client, genie


def test_query_delegates_polling_to_the_sdk():
    client, genie = _client()
    assert client.query("agent", "What were total sales yesterday?", 120) == {
        "called": "start_conversation_and_wait"
    }
    name, args, kwargs = genie.calls[0]
    assert name == "start_conversation_and_wait"
    assert args == ("agent", "What were total sales yesterday?")
    assert kwargs == {"timeout": timedelta(seconds=120)}


def test_follow_up_delegates_polling_to_the_sdk():
    client, genie = _client()
    client.follow_up("agent", "conversation", "And by store?", 90)
    name, args, kwargs = genie.calls[0]
    assert name == "create_message_and_wait"
    assert args == ("agent", "conversation", "And by store?")
    assert kwargs == {"timeout": timedelta(seconds=90)}


def test_create_agent_maps_the_request_body():
    client, genie = _client()
    body = {
        "warehouse_id": "warehouse",
        "title": "Sales",
        "description": "Sales Agent",
        "parent_path": "/Workspace/agents",
        "serialized_space": '{"version":2}',
    }
    client.create_agent(body)
    name, _, kwargs = genie.calls[0]
    assert name == "create_space"
    assert kwargs == body


def test_update_agent_sends_the_etag_and_never_moves_the_agent():
    client, genie = _client()
    body = {
        "warehouse_id": "warehouse",
        "title": "Sales",
        "description": "Sales Agent",
        "parent_path": "/Workspace/agents",
        "serialized_space": '{"version":2}',
    }
    client.update_agent("agent", body, etag="etag-1")
    name, args, kwargs = genie.calls[0]
    assert name == "update_space"
    assert args == ("agent",)
    assert kwargs["etag"] == "etag-1"
    assert "parent_path" not in kwargs


def test_get_agent_requests_the_serialized_definition():
    client, genie = _client()
    client.get_agent("agent")
    name, args, kwargs = genie.calls[0]
    assert name == "get_space"
    assert args == ("agent",)
    assert kwargs == {"include_serialized_space": True}
