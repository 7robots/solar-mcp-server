# FastMCP Cloud Deployment Guide

## Overview

FastMCP Cloud ([fastmcp.cloud](https://fastmcp.cloud)) is a managed hosting platform for MCP servers. It supports FastMCP 2.0 servers and is currently free during beta.

---

## Prerequisites

1. **GitHub account** - for authentication and repository access
2. **GitHub repository** - containing your FastMCP server (public or private)
3. **Python 3.11+** - FastMCP requires Python 3.11 or higher
4. **Valid server file** - Python file with FastMCP server instance

---

## Project Structure

```
my-mcp-server/
├── server.py          # Main server file (required)
├── pyproject.toml     # Dependencies (recommended)
├── requirements.txt   # Alternative to pyproject.toml
├── .env               # Local secrets (DO NOT COMMIT)
├── .gitignore         # Must exclude .env
└── README.md          # Documentation
```

---

## Deployment Steps

### Step 1: Prepare Your Server

**Verify server compatibility:**
```bash
fastmcp inspect server.py
```

**Ensure HTTP transport in entry point:**
```python
if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
```

### Step 2: Push to GitHub

```bash
git init
git add server.py pyproject.toml .gitignore README.md
git commit -m "Initial commit: MCP server for [service]"
gh repo create my-mcp-server --public --source=. --push
```

### Step 3: Deploy on FastMCP Cloud

1. Visit [fastmcp.cloud](https://fastmcp.cloud)
2. Click "Sign in with GitHub"
3. Click "Create Project"
4. Configure:
   - **Name**: Your project name (becomes URL slug)
   - **Repository**: Select your GitHub repo
   - **Entrypoint**: `server.py` (or `server.py:mcp` if named differently)
   - **Authentication**: Toggle for public/private access
5. Click "Deploy"

### Step 4: Connect to Your Server

Your server URL: `https://your-project-name.fastmcp.app/mcp`

**Connect from Claude Desktop:**
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://your-project-name.fastmcp.app/mcp"
    }
  }
}
```

---

## Secrets Management

### Local Development

**Create `.env` file:**
```bash
API_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host/db
```

**Load in Python:**
```python
from dotenv import load_dotenv
load_dotenv()  # Only needed for local development

API_KEY = os.environ.get("API_KEY", "")
```

**Important:** The `load_dotenv()` call is ignored by fastmcp.cloud which injects environment variables directly.

### FastMCP Cloud Secrets

1. Go to your project on fastmcp.cloud
2. Navigate to **Settings** > **Environment Variables**
3. Add each secret:
   - **Name**: Variable name (e.g., `API_KEY`)
   - **Value**: Secret value
4. Click "Save"
5. Redeploy for changes to take effect

**Access in code:**
```python
# Works both locally (with .env) and on fastmcp.cloud
API_KEY = os.environ.get("API_KEY", "")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

---

## Continuous Deployment

FastMCP Cloud automatically redeploys when you push to `main` branch:

```bash
git add .
git commit -m "Update: add new tool"
git push origin main
# Automatic redeploy triggered
```

### Pull Request Previews

Push to a branch and create a PR to get a preview deployment URL for testing before merging.

---

## Troubleshooting

### Common Issues

**"Module not found" errors:**
- Ensure all dependencies are in `pyproject.toml` or `requirements.txt`
- Check that dependency versions are compatible with Python 3.11+

**"Server not responding":**
- Verify entrypoint is correct (`server.py` vs `server.py:mcp`)
- Check that `mcp.run()` uses `transport="http"`
- Ensure `MCP_HOST` defaults to `"0.0.0.0"` not `"127.0.0.1"`

**"Authentication failed":**
- Verify environment variables are set in project settings
- Check variable names match exactly (case-sensitive)
- Redeploy after adding new environment variables

### Viewing Logs

1. Go to your project on fastmcp.cloud
2. Navigate to **Deployments**
3. Click on a deployment to view logs

---

## Best Practices

### Security

- Never commit `.env` files
- Use environment variables for all secrets
- Validate API credentials on startup
- Return generic error messages (don't expose internal details)

### Performance

- Use async/await for all I/O operations
- Implement connection pooling for databases
- Add timeouts to external API calls
- Cache frequently accessed data when appropriate

### Reliability

- Handle all exceptions gracefully
- Return actionable error messages
- Implement retry logic for transient failures
- Log errors for debugging (to stderr, not stdout)

---

## Example pyproject.toml

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "MCP server for [service]"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.0.0,<3",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

---

## Example .gitignore

```gitignore
# Secrets
.env
.env.*
*.env

# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```
