#!/usr/bin/env python3
"""NewsAgent Data — MCP server.

Exposes the NewsAgent Data news API (api.newsagentdata.com) as Model Context
Protocol tools, so AI agents (Claude Desktop, Cursor, any MCP client) can query
scored, classified Russian + English news natively.

Auth: set NEWSAGENT_API_KEY in the environment (free key at
https://newsagentdata.com/signup/?plan=free). Public stats need no key.

Run:  NEWSAGENT_API_KEY=xxx python newsagent_mcp.py   (stdio transport)
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("NEWSAGENT_API_BASE", "https://api.newsagentdata.com")
API_KEY = os.environ.get("NEWSAGENT_API_KEY", "")
TIMEOUT = 20.0

mcp = FastMCP("newsagent-data")


def _headers() -> dict:
    return {"X-API-Key": API_KEY} if API_KEY else {}


def _get(path: str, params: dict) -> dict:
    """Call the API, return parsed JSON or a structured error dict."""
    params = {k: v for k, v in params.items() if v not in (None, "")}
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, headers=_headers(), timeout=TIMEOUT)
    except Exception as e:
        return {"error": f"request failed: {e}"}
    if r.status_code in (401, 422):
        return {"error": "Auth error — set a valid NEWSAGENT_API_KEY "
                         "(free key at https://newsagentdata.com/signup/?plan=free)."}
    if r.status_code == 403:
        return {"error": "403 — your tier doesn't allow this request "
                         "(e.g. /v1/sources needs Standard+; upgrade or narrow the query)."}
    if r.status_code == 429:
        return {"error": "429 — daily quota or burst limit reached for your key."}
    if r.status_code >= 400:
        return {"error": f"{r.status_code}: {r.text[:200]}"}
    try:
        return r.json()
    except Exception:
        return {"error": "non-JSON response"}


def _trim(d: dict, keep: int = 25) -> dict:
    """Cap article lists so responses stay token-light for the model."""
    if isinstance(d, dict) and isinstance(d.get("articles"), list):
        d = dict(d)
        d["articles"] = d["articles"][:keep]
    return d


@mcp.tool()
def get_feed(country: str = "", topic: str = "", language: str = "",
            political_lean: str = "", audience: str = "", min_score: int = 0,
            days: int = 7, limit: int = 20) -> dict:
    """Get a filtered feed of enriched news articles.

    Every article is pre-scored for urgency (0-10), classified by political
    lean, topic, country and audience, and de-duplicated.

    Args:
      country: ISO-2 code, e.g. 'ru', 'ua', 'us', 'mx'. Empty = all.
      topic: one of cyber, sanctions, oil_gas, energy, markets, crypto, ai,
             defense, health, climate, trade, ukraine, middle_east, nuclear,
             elections, diplomacy, rates, terrorism, chips, space, mergers,
             pandemic, agriculture, economy, tech, transport. Empty = all.
      language: 'ru', 'en', 'es', 'pt', etc. Empty = all.
      political_lean: state, official, centrist, liberal, conservative,
             nationalist, opposition, tabloid, neutral.
      audience: trading, media, academic, security, tech, politics.
      min_score: minimum urgency (0-10). Use 7+ for breaking-only.
      days: history window (tier-limited; demo=1, developer=7, standard=90).
      limit: max articles (capped at 50).
    """
    return _trim(_get("/v1/feed", {
        "country": country, "topic": topic, "language": language,
        "political_lean": political_lean, "audience": audience,
        "min_score": min_score, "days": days, "page_size": min(limit, 50),
    }))


@mcp.tool()
def search_news(query: str, min_score: int = 0, language: str = "",
               days: int = 30, limit: int = 20) -> dict:
    """Full-text keyword search across the news archive.

    Args:
      query: search terms (matched against title + content).
      min_score: minimum urgency score (0-10).
      language: 'ru', 'en', etc. Empty = all.
      days: history window (tier-limited).
      limit: max results (capped at 50).
    """
    return _trim(_get("/v1/search", {
        "q": query, "min_score": min_score, "language": language,
        "days": days, "page_size": min(limit, 50),
    }))


@mcp.tool()
def get_breaking(country: str = "", topic: str = "", min_score: int = 7,
                limit: int = 20) -> dict:
    """Get recent breaking news (high urgency). Defaults to urgency >= 7.

    Args:
      country: ISO-2 code. Empty = all.
      topic: topic filter (see get_feed). Empty = all.
      min_score: minimum urgency (default 7).
      limit: max articles (capped at 50).
    """
    return _trim(_get("/v1/breaking", {
        "country": country, "topic": topic, "min_score": min_score,
        "page_size": min(limit, 50),
    }))


@mcp.tool()
def coverage_stats() -> dict:
    """Live coverage stats — total articles, breaking count, today's volume,
    active sources, countries and language counts. No API key required."""
    return _get("/public/stats", {})


@mcp.tool()
def list_sources(limit: int = 50) -> dict:
    """List source catalog metadata (type, language, country, audience,
    political lean). Requires a Standard-tier key or higher; handles are not
    exposed. Use coverage_stats() for public aggregate counts instead."""
    return _trim(_get("/v1/sources", {"page_size": min(limit, 100)}), keep=100)


if __name__ == "__main__":
    mcp.run()
