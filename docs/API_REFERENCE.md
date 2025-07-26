# API Reference

Complete reference for all available Bugcrowd MCP server tools and endpoints.

## Tool Categories

### Organizations
- `get_organizations` - List all accessible organizations
- `get_organization` - Get specific organization details

### Programs  
- `get_programs` - List bug bounty programs
- `get_program` - Get specific program details

### Submissions
- `get_submissions` - List vulnerability submissions
- `get_submission` - Get specific submission details
- `create_submission` - Create new vulnerability report
- `update_submission` - Update existing submission

### Reports
- `get_reports` - Alternative reports endpoint
- `get_report` - Get specific report details

### Assets
- `get_customer_assets` - List security test targets
- `get_customer_asset` - Get specific asset details

### Rewards
- `get_monetary_rewards` - List bounty rewards
- `get_monetary_reward` - Get specific reward details

### Users
- `get_users` - List users in organization
- `get_user` - Get specific user details

### Health
- `server_health` - Check server and API connectivity

## Query Parameters

Most endpoints support query parameters for filtering, pagination, and data inclusion:

- `page[limit]` - Limit number of results
- `page[offset]` - Pagination offset
- `filter[field]=value` - Filter by field value
- `include=relationship` - Include related data
- `sort=field` or `sort=-field` - Sort ascending/descending

## Example Usage

### List Organizations
```python
result = await session.call_tool("get_organizations", {
    "query_params": "page[limit]=5&include=programs"
})
```

### Get Specific Program
```python
result = await session.call_tool("get_program", {
    "id": "program-uuid",
    "query_params": "include=assets,rewards"
})
```

### Create Submission
```python
result = await session.call_tool("create_submission", {
    "data": {
        "title": "XSS Vulnerability",
        "description": "Details of the vulnerability...",
        "program_id": "program-uuid"
    }
})
```

## Response Format

All tools return JSON responses following the Bugcrowd API format:

```json
{
  "data": [...],
  "meta": {
    "total_hits": 10,
    "count": 5
  },
  "links": {
    "self": "/endpoint",
    "next": "/endpoint?page[offset]=5"
  }
}
```