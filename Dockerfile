# NewsAgent Data MCP server — stdio transport
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY newsagent_mcp.py ./

# Provide your key at runtime: -e NEWSAGENT_API_KEY=...
# (public stats work without a key; free key: https://newsagentdata.com/signup/?plan=free)
ENV NEWSAGENT_API_KEY=""

CMD ["python", "newsagent_mcp.py"]
