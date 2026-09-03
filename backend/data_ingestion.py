import os
from gdacs.api import GDACSAPIReader
import httpx
from graph import create_disaster_node, create_alert_node

gdacs_client = GDACSAPIReader()

def ingest_gdacs():
    """Pull latest events from GDACS and write to Neo4j knowledge graph."""
    try:
        events = gdacs_client.latest_events()
        features = events.features if hasattr(events, 'features') else events.get('features', [])
        for event in features:
            # v2.0.0 returns plain dicts
            if isinstance(event, dict):
                props = event.get("properties", {})
                geometry = event.get("geometry", {})
                coords = geometry.get("coordinates", [None, None]) if geometry else [None, None]
                lat = coords[1] if len(coords) > 1 else None
                lon = coords[0] if len(coords) > 0 else None
            else:
                props = event.properties
                lat = event.geometry.coordinates[1] if event.geometry else None
                lon = event.geometry.coordinates[0] if event.geometry else None

            create_alert_node({
                "id": str(props.get("eventid", "")),
                "type": props.get("eventtype", ""),
                "name": props.get("name", ""),
                "severity": props.get("alertlevel", ""),
                "country": props.get("country", ""),
                "lat": lat,
                "lon": lon,
                "date": str(props.get("fromdate", "")),
                "source": "GDACS",
            })
        print(f"[GDACS] Ingested {len(features)} events")
    except Exception as e:
        print(f"[GDACS] Error: {e}")


FEMA_BASE = "https://www.fema.gov/api/open/v2"

def ingest_fema():
    """Pull recent FEMA disaster declarations and write to Neo4j."""
    try:
        resp = httpx.get(
            f"{FEMA_BASE}/DisasterDeclarationsSummaries",
            params={"$top": 50, "$orderby": "declarationDate desc"},
            timeout=30,
        )
        resp.raise_for_status()
        records = resp.json().get("DisasterDeclarationsSummaries", [])
        for r in records:
            create_disaster_node({
                "id": r.get("disasterNumber"),
                "type": r.get("incidentType"),
                "title": r.get("declarationTitle"),
                "state": r.get("state"),
                "date": r.get("declarationDate"),
                "close_date": r.get("incidentEndDate"),
                "source": "FEMA",
            })
        print(f"[FEMA] Ingested {len(records)} disaster declarations")
    except Exception as e:
        print(f"[FEMA] Error: {e}")
