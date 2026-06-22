# NewsAgent Data — MCP server

Query scored, classified Russian & English news from any MCP client (Claude
Desktop, Cursor, Cline, etc.). The server wraps the
[NewsAgent Data API](https://newsagentdata.com) — every article it returns is
already scored for urgency (0–10), classified by political lean, topic, country
and audience, and de-duplicated.

## Tools

| Tool | What it does |
|------|--------------|
| `get_feed` | Filtered feed — by country, topic, language, political lean, audience, min urgency, date range |
| `search_news` | Full-text keyword search across the archive |
| `get_breaking` | Recent high-urgency news (urgency ≥ 7 by default) |
| `coverage_stats` | Live totals — articles, sources, countries, languages (no key) |
| `list_sources` | Source catalog metadata (Standard tier+) |

## Setup

1. Get a free API key: https://newsagentdata.com/signup/?plan=free
2. Install deps: `pip install -r requirements.txt`
3. Add to your MCP client config. **Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "newsagent": {
      "command": "python",
      "args": ["/absolute/path/to/newsagent_mcp.py"],
      "env": { "NEWSAGENT_API_KEY": "your_key_here" }
    }
  }
}
```

**Cursor / Cline**: point the MCP server command at `newsagent_mcp.py` the same way, with `NEWSAGENT_API_KEY` in the env.

4. Restart the client. The five tools appear automatically.

## Example prompts

- *"Get breaking sanctions news from Russia scored 7 or higher."*
- *"Search the news for 'central bank rate' in the last 14 days, English only."*
- *"Compare how state vs opposition sources covered Ukraine this week."* (uses `get_feed` with `political_lean`)
- *"What's the live coverage — how many countries and sources?"*

The agent picks the right tool and filters; results come back pre-scored and
classified, so no NLP pipeline is needed on your side.

## Notes

- Free/Developer tiers have a history window (1–7 days) and daily quotas; the
  server surfaces 401/403/429 as clear errors.
- `list_sources` requires a Standard-tier key; channel handles are never exposed.
- Set `NEWSAGENT_API_BASE` to override the API host (defaults to
  `https://api.newsagentdata.com`).
