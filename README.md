# Bugcrowd MCP Server

A flexible MCP (Model Context Protocol) server providing secure access to the Bugcrowd bug bounty platform API. Compatible with multiple LLM platforms including OpenAI Codex, Claude Code, and direct FastMCP integration.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/unstrike/Bugcrowd_MCP_Server.git
cd Bugcrowd_MCP_Server

# Create virtual environment (using uv recommended)
uv venv
source .venv/bin/activate

# Install all dependencies
uv sync

# Or install manually with uv
uv add mcp httpx openai-agents
```

### 2. Test Installation

```bash
./test/test_server.sh
```

## 🔧 How to Use the Agent

### Method 1: Interactive Example

Run the included example to see the agent in action:

```bash
uv run python3 agents/openai_agent_example.py
```

This launches an interactive session where you can:
- **List programs**: "Show me available bug bounty programs"
- **Check submissions**: "What are recent vulnerability submissions?"
- **View rewards**: "Show me monetary reward information"
- **Explore assets**: "What customer assets are available for testing?"

### Method 2: Direct Python Integration

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

    # Use the agent with Runner
    response = await Runner.run(agent, "Show me the latest bug bounty programs")
```

### Method 3: Multi-Platform LLM Integration

This MCP server works with multiple LLM platforms. Choose your preferred integration method:

#### OpenAI Codex Configuration

Configure the server in your OpenAI Codex configuration file at `~/.codex/config.toml`:

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

#### Claude Code Configuration

For Claude Code users, use the provided JSON configuration template:

1. Copy `docs/claude_code_config.json` to your Claude Code MCP servers directory
2. Update the `cwd` path to match your installation directory
3. Set your Bugcrowd API credentials as environment variables:
   ```bash
   export BUGCROWD_API_USERNAME="your-username"
   export BUGCROWD_API_PASSWORD="your-password"
   ```
4. Add the server using Claude Code's MCP management:
   ```bash
   claude mcp add bugcrowd-mcp \
     -e ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY' \
     -- /path/to/your/Bugcrowd_MCP_Server/bugcrowd_mcp_server.py
   ```
   
   Or import the JSON configuration directly into your Claude Code MCP settings.

#### FastMCP Direct Integration

For direct MCP client integration without LLM wrapper, see `agents/fastmcp_example.py`:

```bash
# Install FastMCP dependencies
uv add mcp

# Run the FastMCP example
uv run python3 agents/fastmcp_example.py
```

**Important**: Replace paths with your actual installation directory and set your Bugcrowd API credentials appropriately for your chosen platform.

## 🛠️ Available Tools

The server provides access to these Bugcrowd API endpoints:

| Category | Tool | Description |
|----------|------|-------------|
| **Organizations** | `get_organizations` | List all accessible organizations |
| | `get_organization` | Get specific organization details |
| **Programs** | `get_programs` | List bug bounty programs |
| | `get_program` | Get specific program details |
| **Submissions** | `get_submissions` | List vulnerability submissions |
| | `get_submission` | Get specific submission details |
| | `create_submission` | Create new vulnerability report |
| | `update_submission` | Update existing submission |
| **Reports** | `get_reports` | Alternative reports endpoint |
| | `get_report` | Get specific report details |
| **Assets** | `get_customer_assets` | List security test targets |
| | `get_customer_asset` | Get specific asset details |
| **Rewards** | `get_monetary_rewards` | List bounty rewards |
| | `get_monetary_reward` | Get specific reward details |
| **Users** | `get_users` | List users in organization |
| | `get_user` | Get specific user details |
| **Health** | `server_health` | Check server and API connectivity |

## 🧪 Testing & Verification

### Server Testing
```bash
# Test MCP server functionality
./test/test_server.sh

# Or run directly with uv
uv run python3 bugcrowd_mcp_server.py
```

### Interactive Testing
```bash
# Run the example agent for interactive testing
uv run python3 agents/openai_agent_example.py
```

## Project Structure

```
├── bugcrowd_mcp_server.py        # Main MCP server implementation
├── pyproject.toml                # Project configuration and dependencies
├── uv.lock                       # Locked dependency versions
├── README.md                     # This documentation
├── LICENSE                       # MIT license
├── agents/
│   └── openai_agent_example.py   # Interactive agent example
|   └── fastmcp_example.py        # FastMCP direct integration example
├── docs/
│   ├── INTEGRATION_GUIDE.md      # Platform integration instructions
│   ├── API_REFERENCE.md          # Complete API documentation
│   ├── architecture_diagram.md   # System architecture documentation
│   ├── claude_code_config.json   # Claude Code configuration template
│   └── config.toml.example       # OpenAI Codex configuration template
└── test/
    └── test_server.sh            # Server testing script
```

## 📚 Documentation

- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Detailed platform integration instructions
- [API Reference](docs/API_REFERENCE.md) - Complete tool and endpoint documentation
- [Architecture Diagram](docs/architecture_diagram.md) - System architecture overview
