"""User journey tests for the API."""

import os

import pytest
import utils.api_utils as utils


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get the base URL for the API."""
    base = os.getenv("CONDA_STORE_BASE_URL", "http://localhost:8080")
    return f"{base}/conda-store"


@pytest.fixture(scope="session")
def token(base_url) -> str:
    """Get the token for the API."""
    return os.getenv("CONDA_STORE_TOKEN", "")


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_admin_user_can_create_environment(
    base_url: str, token: str, specification_path: str
) -> None:
    """Test that an admin user can create an environment."""
    api = utils.API(base_url=base_url, token=token)
    namespace = "default"
    environment = api.create_environment(namespace, specification_path).json()["data"][
        "specification"
    ]["name"]
    api.delete_environment(namespace, environment)


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_admin_login_and_delete_shared_environment(
    base_url: str, specification_path: str
) -> None:
    """Test that an admin can login and create/delete an env in a shared namespace."""
    api = utils.API(base_url=base_url)

    # Create a shared namespace; default permissions for namepace/environment
    # */* is admin
    namespace = api.create_namespace().json()["data"]["name"]
    environment = api.create_environment(
        namespace,
        specification_path,
    ).json()["data"][
        "specification"
    ]["name"]

    api.delete_environment(namespace, environment)
    api.delete_namespace(namespace)


@pytest.mark.user_journey
@pytest.mark.parametrize(
    "specification_path",
    [
        ("tests/user_journeys/test_data/simple_environment.yaml"),
    ],
)
def test_user_login_and_create_shared_environment(
    base_url: str, specification_path: str
) -> None:
    """Test that a user can login and create an environment in a shared namespace."""
    api = utils.API(base_url=base_url)

    # Create a shared namespace; default permissions for namepace/environment
    # */* is admin
    namespace = api.create_namespace().json()["data"]["name"]

    dev_api = utils.API(
        base_url=base_url,
        token=api.create_token(
            namespace,
            "developer",
        ).json()[
            "data"
        ]["token"],
    )

    environment = dev_api.create_environment(
        namespace,
        specification_path,
    ).json()[
        "data"
    ]["specification"]["name"]

    api.delete_environment(namespace, environment)
    api.delete_namespace(namespace)


@pytest.mark.user_journey
def test_admin_delete_environment(base_url: str):
    """Test that an admin can delete environments."""
    specs = ["tests/user_journeys/test_data/simple_environment.yaml"]
    api = utils.API(base_url=base_url)

    # Create a shared namespace; default permissions for namepace/environment
    # */* is admin
    namespace = api.create_namespace().json()["data"]["name"]

    envs = []
    for spec in specs:
        envs.append(
            api.create_environment(namespace, spec).json()["data"]["specification"][
                "name"
            ]
        )

    assert len(api.list_environments(namespace).json()["data"]) == len(specs)

    for env in envs:
        api.delete_environment(namespace, env)

    assert len(api.list_environments(namespace).json()["data"]) == 0
    api.delete_namespace(namespace)


@pytest.mark.user_journey
def test_failed_build_logs(base_url: str):
    """Test that a user can access logs for a failed build."""
    api = utils.API(base_url=base_url)
    namespace = "default"
    build_request = api.create_environment(
        namespace,
        "tests/user_journeys/test_data/broken_environment.yaml",
    ).json()

    assert build_request["data"]["status"] == "FAILED"
    assert (
        "invalidpackagenamefaasdfagksdjfhgaskdf"
        in api.get_logs(build_request["data"]["id"]).text
    )