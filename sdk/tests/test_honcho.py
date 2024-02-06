from honcho import Client, GetSessionResponse, GetMessageResponse
from uuid import uuid1
import pytest

def test_session_creation_retrieval():
    app_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    user_id = str(uuid1())
    created_session = client.create_session(user_id)
    retrieved_session = client.get_session(user_id, created_session.id)
    assert retrieved_session.id == created_session.id
    assert retrieved_session.is_active is True
    assert retrieved_session.location_id == "default"
    assert retrieved_session.session_data == {}


def test_session_multiple_retrieval():
    app_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    user_id = str(uuid1())
    created_session_1 = client.create_session(user_id)
    created_session_2 = client.create_session(user_id)
    response = client.get_sessions(user_id)
    retrieved_sessions = response.sessions

    assert len(retrieved_sessions) == 2
    assert retrieved_sessions[0].id == created_session_1.id
    assert retrieved_sessions[1].id == created_session_2.id


def test_session_update():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    created_session = client.create_session(user_id)
    assert created_session.update({"foo": "bar"})
    retrieved_session = client.get_session(user_id, created_session.id)
    assert retrieved_session.session_data == {"foo": "bar"}


def test_session_deletion():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    created_session = client.create_session(user_id)
    assert created_session.is_active is True
    created_session.delete()
    assert created_session.is_active is False
    retrieved_session = client.get_session(user_id, created_session.id)
    assert retrieved_session.is_active is False
    assert retrieved_session.id == created_session.id


def test_messages():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    created_session = client.create_session(user_id)
    created_session.create_message(is_user=True, content="Hello")
    created_session.create_message(is_user=False, content="Hi")
    retrieved_session = client.get_session(user_id, created_session.id)
    response = retrieved_session.get_messages()
    messages = response.messages
    assert len(messages) == 2
    user_message, ai_message = messages
    assert user_message.content == "Hello"
    assert user_message.is_user is True
    assert ai_message.content == "Hi"
    assert ai_message.is_user is False

def test_rate_limit():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    created_session = client.create_session(user_id)
    with pytest.raises(Exception):
        for _ in range(105):
            created_session.create_message(is_user=True, content="Hello")
            created_session.create_message(is_user=False, content="Hi")

def test_app_id_security():
    app_id_1 = str(uuid1())
    app_id_2 = str(uuid1())
    user_id = str(uuid1())
    client_1 = Client(app_id_1, "http://localhost:8000")
    client_2 = Client(app_id_2, "http://localhost:8000")
    created_session = client_1.create_session(user_id)
    created_session.create_message(is_user=True, content="Hello")
    created_session.create_message(is_user=False, content="Hi")
    with pytest.raises(Exception):
        client_2.get_session(user_id, created_session.id)


def test_paginated_sessions():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    for i in range(10):
        client.create_session(user_id)
    
    page = 1
    page_size = 2
    get_session_response = client.get_sessions(user_id, page=page, page_size=page_size)
    assert len(get_session_response.sessions) == page_size

    assert get_session_response.pages == 5

    new_session_response = get_session_response.next()
    assert new_session_response is not None
    assert isinstance(new_session_response, GetSessionResponse)
    assert len(new_session_response.sessions) == page_size

    final_page = client.get_sessions(user_id, page=5, page_size=page_size)

    assert len(final_page.sessions) == 2
    next_page = final_page.next()
    assert next_page is None


def test_paginated_messages():
    app_id = str(uuid1())
    user_id = str(uuid1())
    client = Client(app_id, "http://localhost:8000")
    created_session = client.create_session(user_id)
    for i in range(10):
        created_session.create_message(is_user=True, content="Hello")
        created_session.create_message(is_user=False, content="Hi")

    page_size = 7
    get_message_response = created_session.get_messages(page=1, page_size=page_size)

    assert get_message_response is not None
    assert isinstance(get_message_response, GetMessageResponse)
    assert len(get_message_response.messages) == page_size

    new_message_response = get_message_response.next()
    
    assert new_message_response is not None
    assert isinstance(new_message_response, GetMessageResponse)
    assert len(new_message_response.messages) == page_size

    final_page = created_session.get_messages(page=3, page_size=page_size)

    assert len(final_page.messages) == 20 - ((3-1) * 7)

    next_page = final_page.next()

    assert next_page is None



