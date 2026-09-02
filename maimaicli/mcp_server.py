"""MCP server exposing maimai-cli as tools (maimai_get / maimai_settings).

Run:  MAIMAI_SESSION=./session.local.json python -m maimaicli.mcp_server
Register it in your MCP client (e.g. ~/.claude.json). Needs the `mcp` extra:
      pip install 'maimai-cli[mcp]'
"""
from __future__ import annotations
import os

from .client import MaimaiClient

SESSION = os.environ.get("MAIMAI_SESSION", "session.local.json")


def _client() -> MaimaiClient:
    return MaimaiClient.from_file(SESSION)


def main():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise SystemExit("MCP server needs the mcp package: pip install 'maimai-cli[mcp]'")

    mcp = FastMCP("maimai")

    @mcp.tool()
    def maimai_get(path: str, params: dict | None = None, post: bool = False) -> dict:
        """Signed GET/POST to any 脉脉 endpoint path under /maimai (e.g. 'user/v4/settings',
        'gossip/v3/stext'). Uses the captured session's access_token + device profile."""
        return _client().get_path(path, params, method="POST" if post else "GET")

    @mcp.tool()
    def maimai_settings() -> dict:
        """GET user/v4/settings — quick session-liveness / whoami-ish check."""
        return _client().settings()

    @mcp.tool()
    def maimai_suggest(chars: str, type: int = 0) -> dict:
        """GET sug/get — 脉脉 search-word suggestions for `chars`."""
        return _client().suggest(chars, type=type)

    mcp.run()


if __name__ == "__main__":
    main()
