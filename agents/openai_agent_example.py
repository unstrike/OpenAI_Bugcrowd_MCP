#!/usr/bin/env python3
"""
Example of using the Bugcrowd MCP server with OpenAI Agents SDK
This demonstrates how to integrate the Bugcrowd API through MCP with OpenAI agents.
"""

import asyncio
import os
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async def main():
    """Example usage of Bugcrowd MCP server with OpenAI Agent."""

    # Ensure environment variables are set
    if not os.getenv("BUGCROWD_API_USERNAME") or not os.getenv("BUGCROWD_API_PASSWORD"):
        print("Error: Please set BUGCROWD_API_USERNAME and BUGCROWD_API_PASSWORD environment variables")
        return

    # Get the project root directory for the server script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    server_script = os.path.join(project_root, "openai_mcp_server.py")

    # Create MCP server connection
    async with MCPServerStdio(
        params={
            "command": "python3",
            "args": [server_script],
            "env": {
                "BUGCROWD_API_USERNAME": os.getenv("BUGCROWD_API_USERNAME"),
                "BUGCROWD_API_PASSWORD": os.getenv("BUGCROWD_API_PASSWORD")
            }
        }
    ) as server:

        # List available tools from the MCP server
        tools = await server.list_tools()
        print("Available Bugcrowd MCP tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Create an agent that uses the Bugcrowd MCP server
        agent = Agent(
            name="Bugcrowd Security Assistant",
            instructions="""
            You are a security assistant with access to the Bugcrowd bug bounty platform.
            You can help users:
            - View bug bounty programs and their details
            - Search and analyze vulnerability submissions
            - Check monetary rewards and bounty information
            - Manage customer assets and security scope
            - Access user and organization information

            Always provide helpful, accurate information about security research and vulnerability management.
            Be mindful of sensitive security information and follow responsible disclosure practices.
            """,
            mcp_servers=[server]
        )

        # Example interaction
        print("\nBugcrowd Security Assistant is ready!")
        print("You can now interact with the agent to:")
        print("- List bug bounty programs: 'Show me available bug bounty programs'")
        print("- Check submissions: 'What are the recent vulnerability submissions?'")
        print("- View rewards: 'Show me the monetary rewards information'")
        print("- And more...")

        # Interactive loop (basic example)
        while True:
            try:
                user_input = input("\nEnter your question (or 'quit' to exit): ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Process the user's request with the agent using Runner
                response = await Runner.run(agent, user_input)
                print(f"\nAssistant: {response}")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    # Make sure you have the required dependencies installed:
    # uv add openai-agents httpx mcp

    asyncio.run(main())
