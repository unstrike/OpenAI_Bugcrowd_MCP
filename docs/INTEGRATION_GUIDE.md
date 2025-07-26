# Integration Guide

Comprehensive guide for integrating the Bugcrowd MCP server with different LLM platforms.

## OpenAI Codex Integration

### Configuration
Configure in your `~/.codex/config.toml`:

```toml
# OpenAI Codex Configuration
model = "gpt-4o"
disable_response_storage = false
request_max_retries = 4
stream_max_retries = 10
stream_idle_timeout_ms = 300000

name = "OpenAI Codex Bugcrowd-MCP"

[mcp_servers.Bugcrowd-MCP]
command = "uv"
args = ["run", "python3", "bugcrowd_mcp_server.py"]
cwd = "/path/to/your/Bugcrowd_MCP_Server"
env = { "BUGCROWD_API_USERNAME" = "your-username", "BUGCROWD_API_PASSWORD" = "your-password" }
description = "Bugcrowd bug bounty platform API access for security research and vulnerability management"
```

### Usage
Once configured, you can use the server through OpenAI Codex CLI directly without running the example scripts.

## Claude Code Integration

### Environment Setup
```bash
export BUGCROWD_API_USERNAME="your-username"
export BUGCROWD_API_PASSWORD="your-password"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Adding the Server
```bash
claude mcp add bugcrowd-mcp \
  -e ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY' \
  -- /path/to/your/Bugcrowd_MCP_Server/bugcrowd_mcp_server.py
```

### JSON Configuration Alternative
Use the provided template in `docs/claude_code_config.json` and import directly into Claude Code MCP settings.

## FastMCP Direct Integration

### Installation
```bash
uv add mcp
```

### Usage Example
See `docs/fastmcp_example.py` for a complete implementation:

```python
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Configure server parameters
server_params = StdioServerParameters(
    command="uv",
    args=["run", "python3", "bugcrowd_mcp_server.py"],
    env={
        "BUGCROWD_API_USERNAME": os.getenv("BUGCROWD_API_USERNAME"),
        "BUGCROWD_API_PASSWORD": os.getenv("BUGCROWD_API_PASSWORD")
    }
)

# Connect and use
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("server_health", {})
```

## OpenAI Agents SDK Integration

### Direct Python Integration
```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
import os

async with MCPServerStdio(
    params={
        "command": "python3",
        "args": ["bugcrowd_mcp_server.py"],
        "env": {
            "BUGCROWD_API_USERNAME": os.getenv("BUGCROWD_API_USERNAME"),
            "BUGCROWD_API_PASSWORD": os.getenv("BUGCROWD_API_PASSWORD")
        }
    }
) as server:
    agent = Agent(
        name="Bugcrowd Security Assistant",
        instructions="Help with security research using Bugcrowd API",
        mcp_servers=[server]
    )
    response = await Runner.run(agent, "Show me the latest bug bounty programs")
```

### Interactive Example
```bash
uv run python3 agents/openai_agent_example.py
```