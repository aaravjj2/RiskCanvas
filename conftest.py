"""Root-level conftest.py — adds apps/api to sys.path so all test imports work
when pytest is invoked from the project root."""
import sys
import os

# Ensure apps/api is on the path for all test imports (main, tenancy_v2, etc.)
_api_root = os.path.join(os.path.dirname(__file__), "apps", "api")
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

# Ignore tests that require special environment setup (mcp.mcp_server package)
collect_ignore = [
    "apps/api/tests/test_mcp_server.py",
]


def pytest_configure(config):
    """Enable asyncio auto mode so async test functions in sub-packages work."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
