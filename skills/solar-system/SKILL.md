---
description: Query and explore solar system data — celestial bodies, moons, positions, and statistics
---

# Solar System MCP Server

This server wraps the [Le Systeme Solaire API](https://api.le-systeme-solaire.net/) to provide structured access to solar system data.

## Data Model

- **Bodies**: Celestial objects (planets, moons, asteroids, comets, dwarf planets) with physical properties (mass, radius, density, gravity, temperature), orbital parameters (semi-major axis, eccentricity, period), and discovery metadata.
- **Known Counts**: Statistics on how many objects are catalogued per category (asteroids, comets, Kuiper belt objects, etc.).
- **Positions**: Ephemeris calculations giving right ascension, declination, azimuth, and altitude for an observer at a given location and time.

## Available Tools

| Tool | Use When |
|------|----------|
| `solar_list_bodies` | Browsing bodies with pagination, filtering by type or planet status, and sorting |
| `solar_get_body` | Getting full details on a single body by ID (e.g., `terre`, `mars`, `lune`) |
| `solar_search_bodies` | Searching by English name (case-insensitive substring match) |
| `solar_filter_bodies` | Filtering by physical properties: radius, gravity, density, moon count |
| `solar_get_moons` | Listing all moons of a specific planet |
| `solar_get_planets` | Quick shortcut for all 8 planets ordered by distance from the Sun |
| `solar_get_dwarf_planets` | Quick shortcut for all dwarf planets |
| `solar_list_known_counts` | Getting catalogue statistics across all categories |
| `solar_get_known_count` | Getting the count for one specific category |
| `solar_calculate_positions` | Computing sky positions from a given latitude/longitude/time |

## Query Tips

- **Body IDs** are lowercase French names: `terre` (Earth), `lune` (Moon), `jupiter`, `mars`, `saturne` (Saturn), `soleil` (Sun).
- All tools accept `response_format`: use `"json"` (default) for structured data or `"markdown"` for human-readable output.
- `solar_list_bodies` supports pagination (`page`, `limit`) and sorting (`order_by`, `order_desc`). Use `body_type` to filter (e.g., `"Planet"`, `"Moon"`, `"Asteroid"`, `"Comet"`, `"Dwarf Planet"`).
- `solar_filter_bodies` supports range filters: `min_radius`/`max_radius`, `min_gravity`/`max_gravity`, `min_density`/`max_density`, and `has_moons`.
- For positions, `latitude` is -90 to +90, `longitude` is -180 to +180. Leave `datetime_utc` empty for current time.
- Start broad (list/search), then drill down (get_body) for details.
