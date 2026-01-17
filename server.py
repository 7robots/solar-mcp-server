"""
MCP Server for Solar System API.

This server provides tools to interact with the Solar System API at
https://api.le-systeme-solaire.net/rest/ for retrieving data about
celestial bodies, known object counts, and calculating positions.
"""

import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# Constants (configurable via environment variables)
API_TOKEN = os.environ.get("SOLAR_API_TOKEN", "")
API_BASE_URL = "https://api.le-systeme-solaire.net/rest"

# Initialize MCP server
mcp = FastMCP(
    "solar-system-mcp",
    instructions="MCP server for exploring solar system data. Use these tools to search, filter, and analyze celestial bodies including planets, moons, asteroids, and comets. You can also calculate real-time positions of objects from any observer location.",
)


# Enums
class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


# Utility functions
def get_headers() -> Dict[str, str]:
    """Get headers for API requests."""
    headers = {"Content-Type": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


async def make_api_request(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make authenticated API request to Solar System API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/{endpoint}",
            headers=get_headers(),
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


def handle_api_error(e: Exception) -> str:
    """Format API errors consistently."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Authentication failed. Check SOLAR_API_TOKEN."
        elif status == 404:
            return "Error: Resource not found."
        elif status == 429:
            return "Error: Rate limit exceeded. Wait before retrying."
        return f"Error: API request failed with status {status}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    return f"Error: {type(e).__name__}: {e}"


def format_body_markdown(body: Dict[str, Any]) -> str:
    """Format a celestial body as markdown."""
    lines = [f"## {body.get('englishName') or body.get('name', 'Unknown')} (ID: {body.get('id', 'N/A')})"]

    body_type = body.get("bodyType")
    if body_type:
        lines.append(f"**Type**: {body_type}")

    is_planet = body.get("isPlanet")
    if is_planet is not None:
        lines.append(f"**Is Planet**: {'Yes' if is_planet else 'No'}")

    # Physical characteristics
    mass = body.get("mass")
    if mass and mass.get("massValue"):
        lines.append(f"**Mass**: {mass['massValue']} x 10^{mass['massExponent']} kg")

    vol = body.get("vol")
    if vol and vol.get("volValue"):
        lines.append(f"**Volume**: {vol['volValue']} x 10^{vol['volExponent']} km³")

    density = body.get("density")
    if density:
        lines.append(f"**Density**: {density} g/cm³")

    gravity = body.get("gravity")
    if gravity:
        lines.append(f"**Surface Gravity**: {gravity} m/s²")

    mean_radius = body.get("meanRadius")
    if mean_radius:
        lines.append(f"**Mean Radius**: {mean_radius} km")

    # Orbital characteristics
    semimajor = body.get("semimajorAxis")
    if semimajor:
        lines.append(f"**Semi-major Axis**: {semimajor:,} km")

    perihelion = body.get("perihelion")
    aphelion = body.get("aphelion")
    if perihelion and aphelion:
        lines.append(f"**Orbit Range**: {perihelion:,} - {aphelion:,} km")

    eccentricity = body.get("eccentricity")
    if eccentricity:
        lines.append(f"**Eccentricity**: {eccentricity}")

    orbital_period = body.get("sideralOrbit")
    if orbital_period:
        lines.append(f"**Orbital Period**: {orbital_period} days")

    rotation_period = body.get("sideralRotation")
    if rotation_period:
        lines.append(f"**Rotation Period**: {rotation_period} hours")

    # Temperature
    avg_temp = body.get("avgTemp")
    if avg_temp:
        lines.append(f"**Average Temperature**: {avg_temp} K")

    # Moons
    moons = body.get("moons")
    if moons:
        moon_names = [m.get("moon", "Unknown") for m in moons[:10]]
        lines.append(f"**Moons** ({len(moons)} total): {', '.join(moon_names)}")
        if len(moons) > 10:
            lines.append(f"  *...and {len(moons) - 10} more*")

    # Around
    around = body.get("aroundPlanet")
    if around:
        lines.append(f"**Orbits**: {around.get('planet', 'Unknown')}")

    # Discovery
    discovered_by = body.get("discoveredBy")
    discovery_date = body.get("discoveryDate")
    if discovered_by or discovery_date:
        discovery = []
        if discovered_by:
            discovery.append(f"by {discovered_by}")
        if discovery_date:
            discovery.append(f"on {discovery_date}")
        lines.append(f"**Discovered**: {' '.join(discovery)}")

    return "\n".join(lines)


def format_position_markdown(position: Dict[str, Any]) -> str:
    """Format a position entry as markdown."""
    lines = [f"### {position.get('name', 'Unknown')}"]

    ra = position.get("ra")
    dec = position.get("dec")
    if ra is not None and dec is not None:
        lines.append(f"**Right Ascension**: {ra}°")
        lines.append(f"**Declination**: {dec}°")

    az = position.get("az")
    alt = position.get("alt")
    if az is not None and alt is not None:
        lines.append(f"**Azimuth**: {az}°")
        lines.append(f"**Altitude**: {alt}°")

    return "\n".join(lines)


# Tool definitions
@mcp.tool()
async def solar_list_bodies(
    limit: int = 20,
    page: int = 1,
    body_type: Optional[str] = None,
    is_planet: Optional[bool] = None,
    order_by: str = "id",
    order_desc: bool = False,
    response_format: str = "json",
) -> str:
    """List celestial bodies in the solar system with optional filtering and pagination.

    Args:
        limit: Max bodies to return per page (1-100, default 20)
        page: Page number (default 1)
        body_type: Filter by body type (e.g., 'Planet', 'Moon', 'Asteroid', 'Comet', 'Dwarf Planet')
        is_planet: Filter to only planets (true) or non-planets (false)
        order_by: Field to sort by (e.g., 'id', 'name', 'density', 'gravity', 'meanRadius')
        order_desc: Sort descending if true (default false)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        limit = max(1, min(100, limit))
        page = max(1, page)

        params = {}

        # Pagination and ordering
        order_dir = "desc" if order_desc else "asc"
        params["order"] = f"{order_by},{order_dir}"
        params["page"] = f"{page},{limit}"

        # Filters
        filters = []
        if body_type:
            filters.append(f"bodyType,eq,{body_type}")
        if is_planet is not None:
            filters.append(f"isPlanet,eq,{str(is_planet).lower()}")

        if filters:
            params["filter[]"] = filters

        result = await make_api_request("bodies", params)
        bodies = result.get("bodies", [])

        if response_format == "markdown":
            if not bodies:
                return "No celestial bodies found matching the criteria."

            lines = ["# Solar System Bodies", ""]
            lines.append(f"Page {page}, showing {len(bodies)} bodies")
            lines.append("")

            for body in bodies:
                lines.append(format_body_markdown(body))
                lines.append("")

            if len(bodies) == limit:
                lines.append(f"*More bodies may be available. Use page={page + 1} for next page.*")

            return "\n".join(lines)

        return json.dumps(
            {
                "page": page,
                "count": len(bodies),
                "bodies": bodies,
            },
            indent=2,
        )
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_get_body(body_id: str, response_format: str = "json") -> str:
    """Get detailed information about a specific celestial body.

    Args:
        body_id: The ID of the celestial body (e.g., 'terre' for Earth, 'lune' for Moon, 'mars')
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        body = await make_api_request(f"bodies/{body_id}")

        if response_format == "markdown":
            return format_body_markdown(body)

        return json.dumps(body, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_search_bodies(
    query: str,
    limit: int = 20,
    response_format: str = "json",
) -> str:
    """Search for celestial bodies by name.

    Args:
        query: Search string to match against body names (case-insensitive)
        limit: Maximum results (1-100, default 20)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        limit = max(1, min(100, limit))

        params = {
            "filter[]": f"englishName,cs,{query}",
            "order": "id,asc",
            "page": f"1,{limit}",
        }

        result = await make_api_request("bodies", params)
        bodies = result.get("bodies", [])

        if not bodies:
            return f"No celestial bodies found matching '{query}'."

        if response_format == "markdown":
            lines = [f"# Search Results: '{query}'", ""]
            lines.append(f"Found {len(bodies)} body(ies)")
            lines.append("")

            for body in bodies:
                lines.append(format_body_markdown(body))
                lines.append("")

            return "\n".join(lines)

        return json.dumps({"count": len(bodies), "bodies": bodies}, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_filter_bodies(
    min_radius: Optional[float] = None,
    max_radius: Optional[float] = None,
    min_gravity: Optional[float] = None,
    max_gravity: Optional[float] = None,
    min_density: Optional[float] = None,
    max_density: Optional[float] = None,
    has_moons: Optional[bool] = None,
    limit: int = 20,
    response_format: str = "json",
) -> str:
    """Filter celestial bodies by physical characteristics.

    Args:
        min_radius: Minimum mean radius in km
        max_radius: Maximum mean radius in km
        min_gravity: Minimum surface gravity in m/s²
        max_gravity: Maximum surface gravity in m/s²
        min_density: Minimum density in g/cm³
        max_density: Maximum density in g/cm³
        has_moons: Filter to bodies with moons (true) or without (false)
        limit: Maximum results (1-100, default 20)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        limit = max(1, min(100, limit))

        filters = []
        if min_radius is not None:
            filters.append(f"meanRadius,ge,{min_radius}")
        if max_radius is not None:
            filters.append(f"meanRadius,le,{max_radius}")
        if min_gravity is not None:
            filters.append(f"gravity,ge,{min_gravity}")
        if max_gravity is not None:
            filters.append(f"gravity,le,{max_gravity}")
        if min_density is not None:
            filters.append(f"density,ge,{min_density}")
        if max_density is not None:
            filters.append(f"density,le,{max_density}")

        params = {
            "order": "meanRadius,desc",
            "page": f"1,{limit}",
        }
        if filters:
            params["filter[]"] = filters

        result = await make_api_request("bodies", params)
        bodies = result.get("bodies", [])

        # Client-side filter for moons (API doesn't support this filter)
        if has_moons is not None:
            if has_moons:
                bodies = [b for b in bodies if b.get("moons")]
            else:
                bodies = [b for b in bodies if not b.get("moons")]

        if not bodies:
            return "No celestial bodies found matching the criteria."

        if response_format == "markdown":
            lines = ["# Filtered Bodies", ""]
            lines.append(f"Found {len(bodies)} body(ies) matching criteria")
            lines.append("")

            for body in bodies:
                lines.append(format_body_markdown(body))
                lines.append("")

            return "\n".join(lines)

        return json.dumps({"count": len(bodies), "bodies": bodies}, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_get_moons(
    planet_id: str,
    response_format: str = "json",
) -> str:
    """Get all moons of a specific planet.

    Args:
        planet_id: The ID of the planet (e.g., 'jupiter', 'saturn', 'terre')
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        params = {
            "filter[]": f"aroundPlanet,eq,{planet_id}",
            "order": "meanRadius,desc",
            "page": "1,100",
        }

        result = await make_api_request("bodies", params)
        moons = result.get("bodies", [])

        if not moons:
            return f"No moons found orbiting '{planet_id}'."

        if response_format == "markdown":
            lines = [f"# Moons of {planet_id.title()}", ""]
            lines.append(f"Found {len(moons)} moon(s)")
            lines.append("")

            for moon in moons:
                lines.append(format_body_markdown(moon))
                lines.append("")

            return "\n".join(lines)

        return json.dumps({"planet": planet_id, "count": len(moons), "moons": moons}, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_list_known_counts(response_format: str = "json") -> str:
    """Get counts of known celestial objects by category.

    Args:
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        result = await make_api_request("knowncount")
        counts = result.get("knowncount", result) if isinstance(result, dict) else result

        if response_format == "markdown":
            lines = ["# Known Object Counts", ""]

            if isinstance(counts, list):
                for item in counts:
                    lines.append(f"- **{item.get('id', 'Unknown')}**: {item.get('knownCount', 'N/A')} (updated: {item.get('updateDate', 'N/A')})")
            else:
                lines.append(f"Total known objects: {counts}")

            return "\n".join(lines)

        return json.dumps(counts, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_get_known_count(category_id: str, response_format: str = "json") -> str:
    """Get the count of known objects for a specific category.

    Args:
        category_id: The category ID (e.g., 'asteroids', 'comets', 'kupierbeltobjects')
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        result = await make_api_request(f"knowncount/{category_id}")

        if response_format == "markdown":
            lines = [f"# Known {category_id.title()}", ""]
            lines.append(f"**Count**: {result.get('knownCount', 'N/A')}")
            lines.append(f"**Last Updated**: {result.get('updateDate', 'N/A')}")
            return "\n".join(lines)

        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_calculate_positions(
    latitude: float,
    longitude: float,
    elevation: float = 0,
    datetime_utc: str = "",
    timezone_offset: int = 0,
    response_format: str = "json",
) -> str:
    """Calculate real-time positions of solar system objects from an observer location.

    Args:
        latitude: Observer latitude (-90 to +90)
        longitude: Observer longitude (-180 to +180)
        elevation: Observer altitude in meters (default 0)
        datetime_utc: Date/time in ISO 8601 UTC format (yyyy-MM-ddThh:mm:ss). Leave empty for current time.
        timezone_offset: Timezone offset from UTC (-12 to +14, default 0)
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        # Validate coordinates
        if not -90 <= latitude <= 90:
            return "Error: Latitude must be between -90 and +90 degrees."
        if not -180 <= longitude <= 180:
            return "Error: Longitude must be between -180 and +180 degrees."
        if not -12 <= timezone_offset <= 14:
            return "Error: Timezone offset must be between -12 and +14."

        # Use current time if not provided
        if not datetime_utc:
            from datetime import datetime, timezone
            datetime_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "lat": latitude,
            "lon": longitude,
            "elev": elevation,
            "datetime": datetime_utc,
            "zone": timezone_offset,
        }

        result = await make_api_request("positions", params)

        if response_format == "markdown":
            lines = ["# Celestial Positions", ""]

            # Location info
            location = result.get("location", {})
            lines.append("## Observer Location")
            lines.append(f"- Latitude: {location.get('lat', latitude)}°")
            lines.append(f"- Longitude: {location.get('lon', longitude)}°")
            lines.append(f"- Elevation: {location.get('elev', elevation)} m")
            lines.append("")

            # Time info
            time_info = result.get("time_info", {})
            lines.append("## Time Information")
            lines.append(f"- UTC: {time_info.get('utc', datetime_utc)}")
            lines.append(f"- Local: {time_info.get('local', 'N/A')}")
            lines.append(f"- Julian Day: {time_info.get('jd', 'N/A')}")
            lines.append("")

            # Positions
            positions = result.get("positions", [])
            lines.append("## Object Positions")
            lines.append("")

            for pos in positions:
                lines.append(format_position_markdown(pos))
                lines.append("")

            return "\n".join(lines)

        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_get_planets(response_format: str = "json") -> str:
    """Get all planets in the solar system.

    Args:
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        params = {
            "filter[]": "isPlanet,eq,true",
            "order": "semimajorAxis,asc",
        }

        result = await make_api_request("bodies", params)
        planets = result.get("bodies", [])

        if response_format == "markdown":
            lines = ["# Planets of the Solar System", ""]
            lines.append(f"Total: {len(planets)} planets")
            lines.append("")

            for planet in planets:
                lines.append(format_body_markdown(planet))
                lines.append("")

            return "\n".join(lines)

        return json.dumps({"count": len(planets), "planets": planets}, indent=2)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
async def solar_get_dwarf_planets(response_format: str = "json") -> str:
    """Get all dwarf planets in the solar system.

    Args:
        response_format: 'json' for structured data or 'markdown' for human-readable
    """
    try:
        params = {
            "filter[]": "bodyType,eq,Dwarf Planet",
            "order": "semimajorAxis,asc",
        }

        result = await make_api_request("bodies", params)
        dwarf_planets = result.get("bodies", [])

        if response_format == "markdown":
            lines = ["# Dwarf Planets of the Solar System", ""]
            lines.append(f"Total: {len(dwarf_planets)} dwarf planets")
            lines.append("")

            for dp in dwarf_planets:
                lines.append(format_body_markdown(dp))
                lines.append("")

            return "\n".join(lines)

        return json.dumps({"count": len(dwarf_planets), "dwarf_planets": dwarf_planets}, indent=2)
    except Exception as e:
        return handle_api_error(e)


if __name__ == "__main__":
    # HTTP transport for fastmcp.cloud
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)
