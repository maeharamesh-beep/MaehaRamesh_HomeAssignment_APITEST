import pytest
import requests


@pytest.fixture(scope="session")
def http_session():
    """
    Session-scoped requests.Session with a shared base URL and default timeout.
    Re-using a single session across all tests improves speed via connection pooling.
    """
    with requests.Session() as session:
        session.headers.update({"Accept": "application/json"})
        yield session


@pytest.fixture(scope="session")
def base_url():
    return "https://jsonplaceholder.typicode.com"
