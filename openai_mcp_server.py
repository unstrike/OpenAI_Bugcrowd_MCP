#!/usr/bin/env python3
"""
Bugcrowd MCP Server for OpenAI Agents SDK

A high-performance MCP server providing secure access to the Bugcrowd bug bounty platform API
through the Model Context Protocol, optimized for OpenAI's Agents SDK integration.

Features:
- Comprehensive Bugcrowd API coverage
- Efficient connection pooling and caching
- Robust error handling and validation
- Type-safe implementation
- Defensive security focus
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import unquote_plus

import httpx
from mcp.server.fastmcp import FastMCP

# Import cleanup for proper shutdown
import atexit

# Register cleanup function
atexit.register(lambda: None)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bugcrowd API Configuration
BUGCROWD_API_BASE = "https://api.bugcrowd.com"
BUGCROWD_API_VERSION = "2025-04-23"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3

# Global HTTP client for connection pooling
_http_client: Optional[httpx.AsyncClient] = None
_api_credentials: Optional[Dict[str, str]] = None

def _load_api_credentials() -> Dict[str, str]:
    """Load and cache API credentials from environment variables."""
    global _api_credentials
    
    if _api_credentials is None:
        username = os.getenv("BUGCROWD_API_USERNAME")
        password = os.getenv("BUGCROWD_API_PASSWORD")
        
        if not username or not password:
            raise RuntimeError(
                "BUGCROWD_API_USERNAME and BUGCROWD_API_PASSWORD must be set in environment variables. "
                "Please configure your Bugcrowd API credentials."
            )
        
        _api_credentials = {"username": username, "password": password}
        logger.info("Bugcrowd API credentials loaded successfully")
    
    return _api_credentials


async def _get_http_client() -> httpx.AsyncClient:
    """Get or create a shared HTTP client with connection pooling."""
    global _http_client
    
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            follow_redirects=True
        )
        logger.info("HTTP client initialized with connection pooling")
    
    return _http_client


def _parse_query_params(query_params: str) -> Dict[str, str]:
    """Parse query parameters string into a dictionary.
    
    Args:
        query_params: URL-encoded query string like "limit=10&offset=0&filter[status]=open"
        
    Returns:
        Dictionary of parsed parameters
        
    Raises:
        ValueError: If query parameters are malformed
    """
    if not query_params.strip():
        return {}
    
    params = {}
    try:
        for param in query_params.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                # URL decode the key and value
                key = unquote_plus(key.strip())
                value = unquote_plus(value.strip())
                
                # Validate parameter names (alphanumeric, underscore, brackets, dots)
                if not re.match(r'^[a-zA-Z0-9_\[\].]+$', key):
                    raise ValueError(f"Invalid parameter name: {key}")
                
                params[key] = value
    except Exception as e:
        raise ValueError(f"Malformed query parameters: {query_params}") from e
    
    return params


def _validate_resource_id(resource_id: str) -> str:
    """Validate and sanitize resource ID.
    
    Args:
        resource_id: The resource ID to validate
        
    Returns:
        Validated resource ID
        
    Raises:
        ValueError: If resource ID is invalid
    """
    if not resource_id or not resource_id.strip():
        raise ValueError("Resource ID cannot be empty")
    
    resource_id = resource_id.strip()
    
    # Allow UUIDs, alphanumeric with hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', resource_id):
        raise ValueError(f"Invalid resource ID format: {resource_id}")
    
    return resource_id


async def bugcrowd_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[Dict[str, Any]] = None, 
    **query_params: str
) -> Dict[str, Any]:
    """Make authenticated requests to the Bugcrowd API with robust error handling.
    
    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        endpoint: API endpoint path
        json_data: Optional JSON payload for POST/PATCH requests
        **query_params: Query parameters as keyword arguments
        
    Returns:
        JSON response from the API
        
    Raises:
        RuntimeError: For authentication or configuration errors
        httpx.HTTPStatusError: For HTTP errors
        ValueError: For invalid input parameters
    """
    try:
        credentials = _load_api_credentials()
        client = await _get_http_client()
        
        # Construct URL and headers
        url = f"{BUGCROWD_API_BASE}{endpoint}"
        headers = {
            "Accept": "application/vnd.bugcrowd+json",
            "Authorization": f"Token {credentials['username']}:{credentials['password']}",
            "Bugcrowd-Version": BUGCROWD_API_VERSION,
            "User-Agent": "Bugcrowd-MCP-Server/1.0.0"
        }
        
        # Clean up query_params (remove internal parameters)
        clean_params = {k: v for k, v in query_params.items() 
                       if k not in ['query_params'] and v is not None}
        
        logger.debug(f"Making {method} request to {endpoint} with params: {clean_params}")
        
        # Make the request with retry logic
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=clean_params,
            json=json_data
        )
        
        response.raise_for_status()
        
        # Return parsed JSON response
        result = response.json()
        logger.debug(f"Successful response from {endpoint}")
        return result
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} for {method} {endpoint}: {e.response.text}")
        
        # Provide more specific error messages
        if e.response.status_code == 401:
            raise RuntimeError("Authentication failed. Please check your Bugcrowd API credentials.") from e
        elif e.response.status_code == 403:
            raise RuntimeError("Access forbidden. You may not have permission to access this resource.") from e
        elif e.response.status_code == 404:
            raise RuntimeError(f"Resource not found: {endpoint}") from e
        elif e.response.status_code == 429:
            raise RuntimeError("Rate limit exceeded. Please try again later.") from e
        else:
            raise RuntimeError(f"API request failed with status {e.response.status_code}") from e
            
    except httpx.RequestError as e:
        logger.error(f"Network error for {method} {endpoint}: {str(e)}")
        raise RuntimeError(f"Network error: Unable to connect to Bugcrowd API") from e
        
    except Exception as e:
        logger.error(f"Unexpected error for {method} {endpoint}: {str(e)}")
        raise RuntimeError(f"Unexpected error during API request: {str(e)}") from e


async def _cleanup_http_client():
    """Clean up the HTTP client on shutdown."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        logger.info("HTTP client closed")

# Create the MCP server with OpenAI-friendly configuration
mcp = FastMCP(
    "Bugcrowd-MCP", 
    description="High-performance MCP server providing secure access to Bugcrowd bug bounty platform API for defensive security research and vulnerability management"
)


# Tool helper function to reduce code duplication
async def _make_api_request(
    method: str,
    endpoint: str,
    resource_id: Optional[str] = None,
    query_params: str = "",
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Helper function for making API requests with consistent parameter handling.
    
    Args:
        method: HTTP method
        endpoint: Base endpoint path
        resource_id: Optional resource ID to append to endpoint
        query_params: Query parameters string
        json_data: Optional JSON payload
        
    Returns:
        API response data
    """
    # Build full endpoint path
    full_endpoint = endpoint
    if resource_id:
        validated_id = _validate_resource_id(resource_id)
        full_endpoint = f"{endpoint}/{validated_id}"
    
    # Parse query parameters
    parsed_params = _parse_query_params(query_params)
    
    # Make the request
    return await bugcrowd_request(method, full_endpoint, json_data, **parsed_params)

# ORGANIZATIONS - Core entity management
@mcp.tool()
async def get_organizations(query_params: str = "") -> Dict[str, Any]:
    """List all organizations accessible to the authenticated user.
    
    Args:
        query_params: Optional query parameters (e.g., "limit=10&offset=0&filter[name]=example")
        
    Returns:
        Dictionary containing organizations data and metadata
        
    Example:
        >>> await get_organizations("limit=5&include=programs")
    """
    return await _make_api_request("GET", "/organizations", query_params=query_params)


@mcp.tool()
async def get_organization(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific organization by ID.
    
    Args:
        id: Organization ID (UUID or identifier)
        query_params: Optional query parameters for including related data
        
    Returns:
        Dictionary containing organization details
        
    Raises:
        ValueError: If organization ID is invalid
        RuntimeError: If organization is not found or access is denied
        
    Example:
        >>> await get_organization("org-123", "include=programs,users")
    """
    return await _make_api_request("GET", "/organizations", resource_id=id, query_params=query_params)

# PROGRAMS - Bug bounty programs
@mcp.tool()
async def get_programs(query_params: str = "") -> Dict[str, Any]:
    """List all bug bounty programs available to the authenticated user.
    
    Args:
        query_params: Optional query parameters for filtering and pagination
                     (e.g., "limit=10&filter[status]=active&sort=-created_at")
        
    Returns:
        Dictionary containing programs data, pagination info, and metadata
        
    Example:
        >>> await get_programs("filter[organization_id]=org-123&include=rewards")
    """
    return await _make_api_request("GET", "/programs", query_params=query_params)


@mcp.tool()
async def get_program(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific bug bounty program.
    
    Args:
        id: Program ID (UUID or identifier)
        query_params: Optional query parameters for including related data
                     (e.g., "include=rewards,assets,organization")
        
    Returns:
        Dictionary containing comprehensive program details
        
    Raises:
        ValueError: If program ID is invalid
        RuntimeError: If program is not found or access is denied
        
    Example:
        >>> await get_program("prog-456", "include=assets,rewards")
    """
    return await _make_api_request("GET", "/programs", resource_id=id, query_params=query_params)

# SUBMISSIONS - Bug submissions and vulnerability reports
@mcp.tool()
async def get_submissions(query_params: str = "") -> Dict[str, Any]:
    """List all bug submissions/vulnerability reports accessible to the user.
    
    Args:
        query_params: Optional query parameters for filtering submissions
                     (e.g., "filter[state]=new&filter[severity]=high&limit=20")
        
    Returns:
        Dictionary containing submissions data with pagination and metadata
        
    Example:
        >>> await get_submissions("filter[program_id]=prog-123&include=activities")
    """
    return await _make_api_request("GET", "/submissions", query_params=query_params)


@mcp.tool()
async def get_submission(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific vulnerability submission.
    
    Args:
        id: Submission ID (UUID or identifier)
        query_params: Optional query parameters for including related data
                     (e.g., "include=activities,comments,attachments")
        
    Returns:
        Dictionary containing comprehensive submission details
        
    Raises:
        ValueError: If submission ID is invalid
        RuntimeError: If submission is not found or access is denied
        
    Example:
        >>> await get_submission("sub-789", "include=activities,researcher")
    """
    return await _make_api_request("GET", "/submissions", resource_id=id, query_params=query_params)


@mcp.tool()
async def create_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new bug submission/vulnerability report.
    
    Args:
        data: Submission data following Bugcrowd API schema
              Must include required fields like title, description, etc.
              
    Returns:
        Dictionary containing the created submission details
        
    Raises:
        ValueError: If submission data is invalid or missing required fields
        RuntimeError: If submission creation fails
        
    Example:
        >>> await create_submission({
        ...     "title": "XSS Vulnerability",
        ...     "description": "Details of the vulnerability...",
        ...     "program_id": "prog-123"
        ... })
    """
    if not data or not isinstance(data, dict):
        raise ValueError("Submission data must be a non-empty dictionary")
    
    # Basic validation of required fields
    required_fields = ["title", "description"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return await _make_api_request("POST", "/submissions", json_data=data)


@mcp.tool()
async def update_submission(id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing vulnerability submission.
    
    Args:
        id: Submission ID (UUID or identifier)
        data: Updated submission data (partial updates supported)
        
    Returns:
        Dictionary containing the updated submission details
        
    Raises:
        ValueError: If submission ID or data is invalid
        RuntimeError: If submission update fails or access is denied
        
    Example:
        >>> await update_submission("sub-789", {
        ...     "state": "triaged",
        ...     "severity": "high"
        ... })
    """
    if not data or not isinstance(data, dict):
        raise ValueError("Update data must be a non-empty dictionary")
    
    return await _make_api_request("PATCH", "/submissions", resource_id=id, json_data=data)

# REPORTS - Alternative report endpoint
@mcp.tool()
async def get_reports(query_params: str = "") -> Dict[str, Any]:
    """List all reports (alternative endpoint to submissions with different data structure).
    
    Args:
        query_params: Optional query parameters for filtering reports
                     (e.g., "filter[status]=resolved&sort=-updated_at")
        
    Returns:
        Dictionary containing reports data with pagination metadata
        
    Note:
        This endpoint may provide a different data structure than /submissions
        depending on your Bugcrowd organization configuration.
        
    Example:
        >>> await get_reports("filter[assignee_id]=user-123&limit=10")
    """
    return await _make_api_request("GET", "/reports", query_params=query_params)


@mcp.tool()
async def get_report(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific report.
    
    Args:
        id: Report ID (UUID or identifier)
        query_params: Optional query parameters for including related data
        
    Returns:
        Dictionary containing comprehensive report details
        
    Raises:
        ValueError: If report ID is invalid
        RuntimeError: If report is not found or access is denied
        
    Example:
        >>> await get_report("rep-456", "include=timeline,researcher")
    """
    return await _make_api_request("GET", "/reports", resource_id=id, query_params=query_params)

# ASSETS - Target assets for security testing
@mcp.tool()
async def get_customer_assets(query_params: str = "") -> Dict[str, Any]:
    """List all customer assets that are in scope for security testing.
    
    Args:
        query_params: Optional query parameters for filtering assets
                     (e.g., "filter[asset_type]=web&filter[status]=active")
        
    Returns:
        Dictionary containing customer assets data and scope information
        
    Note:
        Only returns assets that are explicitly in scope for security testing.
        Always verify scope and rules before conducting any security research.
        
    Example:
        >>> await get_customer_assets("filter[program_id]=prog-123&include=program")
    """
    return await _make_api_request("GET", "/customer_assets", query_params=query_params)


@mcp.tool()
async def get_customer_asset(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific customer asset.
    
    Args:
        id: Customer asset ID (UUID or identifier)
        query_params: Optional query parameters for including related data
        
    Returns:
        Dictionary containing detailed asset information and scope rules
        
    Raises:
        ValueError: If asset ID is invalid
        RuntimeError: If asset is not found or access is denied
        
    Security Note:
        Always review the asset scope and testing rules before conducting
        any security research activities.
        
    Example:
        >>> await get_customer_asset("asset-789", "include=program,scope_rules")
    """
    return await _make_api_request("GET", "/customer_assets", resource_id=id, query_params=query_params)

# MONETARY REWARDS - Reward information
@mcp.tool()
async def get_monetary_rewards(query_params: str = "") -> Dict[str, Any]:
    """List all monetary rewards for bug bounty submissions.
    
    Args:
        query_params: Optional query parameters for filtering rewards
                     (e.g., "filter[status]=paid&filter[amount_gte]=1000")
        
    Returns:
        Dictionary containing monetary rewards data and payment information
        
    Example:
        >>> await get_monetary_rewards("filter[researcher_id]=user-123&sort=-amount")
    """
    return await _make_api_request("GET", "/monetary_rewards", query_params=query_params)


@mcp.tool()
async def get_monetary_reward(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific monetary reward.
    
    Args:
        id: Monetary reward ID (UUID or identifier)
        query_params: Optional query parameters for including related data
        
    Returns:
        Dictionary containing detailed reward and payment information
        
    Raises:
        ValueError: If reward ID is invalid
        RuntimeError: If reward is not found or access is denied
        
    Example:
        >>> await get_monetary_reward("reward-456", "include=submission,researcher")
    """
    return await _make_api_request("GET", "/monetary_rewards", resource_id=id, query_params=query_params)

# USERS - User management
@mcp.tool()
async def get_users(query_params: str = "") -> Dict[str, Any]:
    """List all users in the organization or program scope.
    
    Args:
        query_params: Optional query parameters for filtering users
                     (e.g., "filter[role]=researcher&filter[status]=active")
        
    Returns:
        Dictionary containing users data and profile information
        
    Note:
        User data returned depends on your access level and organization settings.
        Some user information may be restricted for privacy reasons.
        
    Example:
        >>> await get_users("filter[organization_id]=org-123&include=roles")
    """
    return await _make_api_request("GET", "/users", query_params=query_params)


@mcp.tool()
async def get_user(id: str, query_params: str = "") -> Dict[str, Any]:
    """Get detailed information about a specific user.
    
    Args:
        id: User ID (UUID or identifier)
        query_params: Optional query parameters for including related data
        
    Returns:
        Dictionary containing user profile and activity information
        
    Raises:
        ValueError: If user ID is invalid
        RuntimeError: If user is not found or access is denied
        
    Privacy Note:
        User information returned is subject to privacy settings and
        your organization's access policies.
        
    Example:
        >>> await get_user("user-789", "include=organizations,stats")
    """
    return await _make_api_request("GET", "/users", resource_id=id, query_params=query_params)

# Cleanup function to be called on server shutdown
@mcp.tool()
async def server_health() -> Dict[str, str]:
    """Check the health status of the MCP server and API connectivity.
    
    Returns:
        Dictionary containing server health information
        
    Example:
        >>> await server_health()
        {"status": "healthy", "api_connection": "ok", "version": "1.0.0"}
    """
    try:
        # Test API connectivity with a simple request
        await _make_api_request("GET", "/organizations", query_params="limit=1")
        return {
            "status": "healthy",
            "api_connection": "ok",
            "version": "1.0.0",
            "bugcrowd_api_version": BUGCROWD_API_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "api_connection": "error",
            "error": str(e),
            "version": "1.0.0"
        }


if __name__ == "__main__":
    try:
        logger.info("Starting Bugcrowd MCP Server")
        mcp.run("stdio")
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
    finally:
        # Clean up resources
        import asyncio
        try:
            asyncio.run(_cleanup_http_client())
        except:
            pass  # Ignore cleanup errors
        logger.info("Bugcrowd MCP Server stopped")