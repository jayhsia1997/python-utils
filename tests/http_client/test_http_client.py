"""
test http client
"""
import pytest
import respx
from httpx import Response
from http_client import http_client
from http_client.http_client import HttpOptions


def test_options():
    url = "https://localhost:8000/"
    session = http_client.create(url=url)\
        .timeout(30) \
        .retry(10, 3) \
        .add_query('q1', 1) \
        .add_query('q1', 2) \
        .add_form('foo', 2) \
        .add_file('foo', 'a') \
        .add_header('x-a', 'aa') \
        .add_header('x-b', 'aa') \
        .add_cookie('foo', 'bar') \
        .add_json({'name': '1'})
    assert session.options == HttpOptions(
        url=url,
        timeout=30,
        max_retries=10,
        retry_interval=3,
        query={'q1': 2},
        form={'foo': 2},
        files={'foo': 'a'},
        headers={'x-a': 'aa', 'x-b': 'aa'},
        cookies={'foo': 'bar'},
        json={'name': '1'}
    )


@respx.mock
@pytest.mark.asyncio
async def test_get():
    url = "https://localhost:8000/"
    params = {"name": "test"}
    mock_resp = Response(
        status_code=204,
        text="test"
    )
    mock_route = respx.get(url=url, params=params) \
        .mock(return_value=mock_resp)

    response = await http_client.create(url=url) \
        .add_query(params) \
        .aget()
    assert mock_route.called
    assert response.status_code == 204
    assert response.text == "test"
