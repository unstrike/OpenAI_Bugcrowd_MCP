#!/usr/bin/env python3
"""
FastMCP example for Bugcrowd MCP server
Demonstrates direct FastMCP integration without OpenAI Agents SDK dependency
"""

import asyncio
import os
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    """Example usage of Bugcrowd MCP server with FastMCP client."""
    
    # Ensure environment variables are set
    if not os.getenv("BUGCROWD_API_USERNAME") or not os.getenv("BUGCROWD_API_PASSWORD"):
        print("Error: Please set BUGCROWD_API_USERNAME and BUGCROWD_API_PASSWORD environment variables")
        return

    # Get the project root directory for the server script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    server_script = os.path.join(project_root, "bugcrowd_mcp_server.py")

    # Configure server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python3", server_script],
        env={
            "BUGCROWD_API_USERNAME": os.getenv("BUGCROWD_API_USERNAME"),
            "BUGCROWD_API_PASSWORD": os.getenv("BUGCROWD_API_PASSWORD")
        }
    )

    # Connect to MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available Bugcrowd MCP tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Example: Check server health
            print("\nChecking server health...")
            health_result = await session.call_tool("server_health", {})
            print(f"Health status: {health_result.content}")
            
            # Example: List organizations
            print("\nListing organizations...")
            orgs_result = await session.call_tool("get_organizations", {"query_params": "page[limit]=5"})
            print(f"Organizations: {orgs_result.content}")
            
            # Example: List programs
            print("\nListing bug bounty programs...")
            programs_result = await session.call_tool("get_programs", {"query_params": "page[limit]=3"})
            print(f"Programs: {programs_result.content}")

if __name__ == "__main__":
    asyncio.run(main())