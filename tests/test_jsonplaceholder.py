"""
API Tests — JSONPlaceholder (https://jsonplaceholder.typicode.com)
==================================================================
JSONPlaceholder is a free, public REST API used for prototyping and testing.
It provides fake data for posts, comments, users, todos, albums, and photos.

Why JSONPlaceholder?
- No API key required — zero setup friction
- Reliable SLA suitable for CI/CD pipelines
- Supports full CRUD surface (GET / POST / PUT / DELETE)
- Returns predictable, well-structured JSON
- Listed in the public-apis repository

Test Coverage
-------------
TC-01  GET /posts              — collection endpoint: status, size, schema
TC-02  GET /posts/{id}         — single resource: parametrised over valid IDs
TC-03  GET /posts/{id}         — error handling: parametrised over invalid IDs
TC-04  POST /posts             — resource creation: status 201, echo of payload
TC-05  GET /posts?userId={id}  — query-param filtering: parametrised over userIds
TC-06  GET /users/{id}         — user schema: required fields present
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_POST_FIELDS = {"userId", "id", "title", "body"}
REQUIRED_USER_FIELDS = {"id", "name", "username", "email", "address", "phone", "website"}


def assert_post_schema(post: dict) -> None:
    """Assert that a post object contains all required fields with correct types."""
    missing = REQUIRED_POST_FIELDS - post.keys()
    assert not missing, f"Post is missing fields: {missing}"
    assert isinstance(post["id"], int), "Post 'id' must be an integer"
    assert isinstance(post["userId"], int), "Post 'userId' must be an integer"
    assert isinstance(post["title"], str) and post["title"], "Post 'title' must be a non-empty string"
    assert isinstance(post["body"], str) and post["body"], "Post 'body' must be a non-empty string"


# ---------------------------------------------------------------------------
# TC-01  GET /posts — collection validation
# ---------------------------------------------------------------------------

class TestGetAllPosts:
    """
    Validates the /posts collection endpoint.

    Why: Ensures the primary resource endpoint is healthy, returns the correct
    HTTP status, delivers a JSON array, and that every item in the collection
    conforms to the expected schema.  A single test exercises the whole dataset
    so any server-side regression (truncated list, broken schema) is caught.
    """

    def test_status_and_content_type(self, http_session, base_url):
        response = http_session.get(f"{base_url}/posts", timeout=10)
        assert response.status_code == 200, (
            f"Expected 200 but got {response.status_code}"
        )
        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Response Content-Type should be application/json"
        )

    def test_returns_100_posts(self, http_session, base_url):
        response = http_session.get(f"{base_url}/posts", timeout=10)
        posts = response.json()
        assert isinstance(posts, list), "Response body should be a JSON array"
        assert len(posts) == 100, f"Expected 100 posts, got {len(posts)}"

    def test_all_posts_have_valid_schema(self, http_session, base_url):
        posts = http_session.get(f"{base_url}/posts", timeout=10).json()
        for post in posts:
            assert_post_schema(post)


# ---------------------------------------------------------------------------
# TC-02  GET /posts/{id} — valid IDs (parametrised)
# ---------------------------------------------------------------------------

class TestGetSinglePost:
    """
    Validates retrieval of individual posts by ID.

    Why: Parametrising over boundary and mid-range values (1, 50, 100) gives
    confidence that the endpoint works across the full range of valid IDs
    without duplicating test code.  Each case independently checks status,
    the correct ID is echoed back, and the schema is intact.
    """

    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_valid_post_id_returns_200(self, http_session, base_url, post_id):
        response = http_session.get(f"{base_url}/posts/{post_id}", timeout=10)
        assert response.status_code == 200, (
            f"Expected 200 for post {post_id}, got {response.status_code}"
        )

    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_returned_id_matches_requested_id(self, http_session, base_url, post_id):
        post = http_session.get(f"{base_url}/posts/{post_id}", timeout=10).json()
        assert post["id"] == post_id, (
            f"Requested post {post_id} but response contained id={post['id']}"
        )

    @pytest.mark.parametrize("post_id", [1, 50, 100])
    def test_single_post_schema(self, http_session, base_url, post_id):
        post = http_session.get(f"{base_url}/posts/{post_id}", timeout=10).json()
        assert_post_schema(post)


# ---------------------------------------------------------------------------
# TC-03  GET /posts/{id} — invalid IDs return 404 (parametrised)
# ---------------------------------------------------------------------------

class TestGetInvalidPost:
    """
    Validates error handling for non-existent resources.

    Why: A robust API must return 404 for unknown IDs rather than 200 with an
    empty body or a 500 error.  Parametrising over several out-of-range values
    (0, negative, very large) covers different edge cases efficiently.
    """

    @pytest.mark.parametrize("post_id", [0, -1, 9999])
    def test_invalid_post_id_returns_404(self, http_session, base_url, post_id):
        response = http_session.get(f"{base_url}/posts/{post_id}", timeout=10)
        assert response.status_code == 404, (
            f"Expected 404 for non-existent post {post_id}, got {response.status_code}"
        )

    @pytest.mark.parametrize("post_id", [0, -1, 9999])
    def test_invalid_post_returns_empty_object(self, http_session, base_url, post_id):
        """JSONPlaceholder returns {} for 404 responses — validate that contract."""
        body = http_session.get(f"{base_url}/posts/{post_id}", timeout=10).json()
        assert body == {}, (
            f"Expected empty object for missing post {post_id}, got: {body}"
        )


# ---------------------------------------------------------------------------
# TC-04  POST /posts — resource creation
# ---------------------------------------------------------------------------

class TestCreatePost:
    """
    Validates the POST /posts endpoint.

    Why: Ensures the API accepts a well-formed payload, responds with HTTP 201
    (Created), and echoes back the submitted fields plus a new assigned ID.
    This confirms the create contract without side effects (JSONPlaceholder
    does not persist data between requests).
    """

    _PAYLOAD = {
        "title": "Automation Test Post",
        "body": "This post was created by an automated test.",
        "userId": 1,
    }

    def test_create_post_returns_201(self, http_session, base_url):
        response = http_session.post(f"{base_url}/posts", json=self._PAYLOAD, timeout=10)
        assert response.status_code == 201, (
            f"Expected 201 Created, got {response.status_code}"
        )

    def test_create_post_response_contains_payload_fields(self, http_session, base_url):
        body = http_session.post(f"{base_url}/posts", json=self._PAYLOAD, timeout=10).json()
        assert body["title"] == self._PAYLOAD["title"]
        assert body["body"] == self._PAYLOAD["body"]
        assert body["userId"] == self._PAYLOAD["userId"]

    def test_create_post_response_has_new_id(self, http_session, base_url):
        body = http_session.post(f"{base_url}/posts", json=self._PAYLOAD, timeout=10).json()
        assert "id" in body, "Response should contain a generated 'id' field"
        assert isinstance(body["id"], int), "'id' should be an integer"


# ---------------------------------------------------------------------------
# TC-05  GET /posts?userId={id} — query-parameter filtering (parametrised)
# ---------------------------------------------------------------------------

class TestFilterPostsByUser:
    """
    Validates the userId query-parameter filter on /posts.

    Why: Filtering is one of the most commonly used API features.
    Parametrising over three different user IDs confirms that the filter
    correctly scopes results and that every returned post belongs to the
    requested user — this would catch off-by-one or ignored-parameter bugs.
    """

    @pytest.mark.parametrize("user_id", [1, 3, 7])
    def test_filter_returns_only_matching_user_posts(self, http_session, base_url, user_id):
        posts = http_session.get(
            f"{base_url}/posts", params={"userId": user_id}, timeout=10
        ).json()
        assert isinstance(posts, list), "Filtered response should be a JSON array"
        assert len(posts) > 0, f"Expected at least one post for userId={user_id}"
        for post in posts:
            assert post["userId"] == user_id, (
                f"Post {post['id']} has userId={post['userId']}, expected {user_id}"
            )

    @pytest.mark.parametrize("user_id", [1, 3, 7])
    def test_filter_returns_10_posts_per_user(self, http_session, base_url, user_id):
        """JSONPlaceholder assigns exactly 10 posts per user."""
        posts = http_session.get(
            f"{base_url}/posts", params={"userId": user_id}, timeout=10
        ).json()
        assert len(posts) == 10, (
            f"Expected 10 posts for userId={user_id}, got {len(posts)}"
        )


# ---------------------------------------------------------------------------
# TC-06  GET /users/{id} — user schema validation (parametrised)
# ---------------------------------------------------------------------------

class TestGetUser:
    """
    Validates the /users endpoint schema.

    Why: The user resource is used as a foreign key by posts and todos.
    Ensuring that required top-level fields are present and non-empty guards
    against schema drift.  Parametrising over three user IDs checks consistency
    across multiple records without writing repetitive test functions.
    """

    @pytest.mark.parametrize("user_id", [1, 5, 10])
    def test_user_has_required_fields(self, http_session, base_url, user_id):
        user = http_session.get(f"{base_url}/users/{user_id}", timeout=10).json()
        missing = REQUIRED_USER_FIELDS - user.keys()
        assert not missing, f"User {user_id} is missing fields: {missing}"

    @pytest.mark.parametrize("user_id", [1, 5, 10])
    def test_user_email_is_valid_format(self, http_session, base_url, user_id):
        user = http_session.get(f"{base_url}/users/{user_id}", timeout=10).json()
        email = user.get("email", "")
        assert "@" in email and "." in email.split("@")[-1], (
            f"User {user_id} email '{email}' does not look like a valid email address"
        )

    @pytest.mark.parametrize("user_id", [1, 5, 10])
    def test_user_id_matches_request(self, http_session, base_url, user_id):
        user = http_session.get(f"{base_url}/users/{user_id}", timeout=10).json()
        assert user["id"] == user_id, (
            f"Requested user {user_id} but got id={user['id']}"
        )
