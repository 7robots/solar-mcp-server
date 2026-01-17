# Solar System MCP Server

An MCP server for exploring solar system data via the [Le Systeme Solaire API](https://api.le-systeme-solaire.net). Query celestial bodies, calculate sky positions, and retrieve astronomical data.

**Live server:** `https://solar-mcp-server.fastmcp.app/mcp`

## Quick Start

Add to your Claude Desktop config (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "solar-system": {
      "url": "https://solar-mcp-server.fastmcp.app/mcp"
    }
  }
}
```

## Tools

### Browsing Bodies

| Tool | Description |
|------|-------------|
| `solar_list_bodies` | List celestial bodies with filtering and pagination |
| `solar_get_body` | Get detailed info about a specific body by ID |
| `solar_search_bodies` | Search bodies by name |
| `solar_filter_bodies` | Filter by physical characteristics (radius, gravity, density) |

### Specific Queries

| Tool | Description |
|------|-------------|
| `solar_get_planets` | Get all 8 planets ordered by distance from Sun |
| `solar_get_dwarf_planets` | Get dwarf planets (Pluto, Ceres, Eris, etc.) |
| `solar_get_moons` | Get all moons orbiting a specific planet |

### Statistics & Counts

| Tool | Description |
|------|-------------|
| `solar_list_known_counts` | Get counts of known objects by category |
| `solar_get_known_count` | Get count for a specific category |

### Position Calculations

| Tool | Description |
|------|-------------|
| `solar_calculate_positions` | Calculate real-time sky positions from an observer location |

## Examples

**Get all planets:**
```
solar_get_planets(response_format="markdown")
```

**Search for a body:**
```
solar_search_bodies(query="Europa")
```

**Get Jupiter's moons:**
```
solar_get_moons(planet_id="jupiter", response_format="markdown")
```

**Find large bodies with moons:**
```
solar_filter_bodies(min_radius=1000, has_moons=True)
```

**Calculate tonight's sky positions from New York:**
```
solar_calculate_positions(
    latitude=40.7128,
    longitude=-74.0060,
    elevation=10,
    datetime_utc="2025-01-17T22:00:00"
)
```

**List asteroids:**
```
solar_list_bodies(body_type="Asteroid", limit=50)
```

## Body IDs

Common body IDs for `solar_get_body`:

| Body | ID |
|------|-----|
| Sun | `soleil` |
| Mercury | `mercure` |
| Venus | `venus` |
| Earth | `terre` |
| Moon | `lune` |
| Mars | `mars` |
| Jupiter | `jupiter` |
| Saturn | `saturne` |
| Uranus | `uranus` |
| Neptune | `neptune` |
| Pluto | `pluton` |

## Response Formats

All tools support two response formats:

- **`json`** (default) - Structured data for programmatic use
- **`markdown`** - Human-readable formatted output

## Self-Hosting

### Local Development

```bash
git clone https://github.com/yourusername/solar-mcp-server
cd solar-mcp-server

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Optional: Set API token
export SOLAR_API_TOKEN=your-bearer-token

# Run server
python server.py
```

### Deploy to FastMCP Cloud

1. Fork/clone this repository
2. Visit [fastmcp.cloud](https://fastmcp.cloud) and sign in with GitHub
3. Create a new project and select your repository
4. Set entrypoint to `server.py`
5. (Optional) Add `SOLAR_API_TOKEN` environment variable
6. Deploy

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SOLAR_API_TOKEN` | Bearer token for API authentication | No |
| `MCP_HOST` | Host to bind to (default: `0.0.0.0`) | No |
| `MCP_PORT` | Port to bind to (default: `8000`) | No |

## API Reference

This server wraps the [Le Systeme Solaire REST API](https://api.le-systeme-solaire.net/rest/):

- **`/bodies`** - All celestial bodies with filtering
- **`/bodies/{id}`** - Single body details
- **`/knowncount`** - Object count statistics
- **`/positions`** - Ephemeris calculations

## License

MIT
