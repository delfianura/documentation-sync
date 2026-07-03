# GitBook MCP Access Patterns

Reference for accessing GDP Labs GitBook documentation via MCP endpoint.

## Endpoint

```
https://gdplabs.gitbook.io/sdk/~gitbook/mcp
```

## Available Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `searchDocumentation` | Search across all documentation | Finding pages by topic/keyword |
| `getPage` | Fetch full markdown of a specific page | Reading complete page content |

## Tool Schemas

### searchDocumentation

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query string"
    }
  },
  "required": ["query"]
}
```

### getPage

```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "Full URL of the page to fetch"
    }
  },
  "required": ["url"]
}
```

## Usage Examples

### Search Documentation

```bash
curl -s "https://gdplabs.gitbook.io/sdk/~gitbook/mcp" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "searchDocumentation",
      "arguments": {
        "query": "tutorials inference"
      }
    },
    "id": 1
  }'
```

### Get Page Content

```bash
curl -s "https://gdplabs.gitbook.io/sdk/~gitbook/mcp" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "getPage",
      "arguments": {
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker"
      }
    },
    "id": 2
  }'
```

### Get Index Pages (List All Content)

**Tutorials index:**
```bash
curl -s "https://gdplabs.gitbook.io/sdk/~gitbook/mcp" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "getPage",
      "arguments": {
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials"
      }
    },
    "id": 3
  }'
```

**Guides index:**
```bash
curl -s "https://gdplabs.gitbook.io/sdk/~gitbook/mcp" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "getPage",
      "arguments": {
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides"
      }
    },
    "id": 4
  }'
```

## Response Format

Responses use Server-Sent Events (SSE) format:

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"..."}]}}
```

To extract the content:
```bash
| grep -o 'data:.*' | sed 's/^data: //' | jq -r '.result.content[0].text'
```

## Key URLs

| Content | URL |
|---------|-----|
| SDK Root | `https://gdplabs.gitbook.io/sdk/gen-ai-sdk` |
| Tutorials | `https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials` |
| Guides | `https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides` |
| LM Invoker | `https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker` |
| RAG Pipeline | `https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline` |

## Notes

- MCP endpoint requires both `application/json` and `text/event-stream` Accept headers
- Responses are streamed as SSE (Server-Sent Events)
- Use `getPage` on index pages (tutorials, guides) to get full content listing
- Use `searchDocumentation` to find specific topics across all docs
- No authentication required for read access
