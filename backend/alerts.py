from fastapi import APIRouter
from graph import run_cypher

router = APIRouter()


@router.get("/recent")
def recent_alerts():
    """Return most recent events — GDACS alerts + FEMA disasters."""
    alerts = run_cypher(
        "MATCH (a:Alert) RETURN a.name AS name, a.type AS type, a.severity AS severity, a.country AS location, a.date AS date, a.source AS source ORDER BY a.date DESC LIMIT 10"
    )
    disasters = run_cypher(
        "MATCH (d:Disaster) RETURN d.title AS name, d.type AS type, '' AS severity, d.state AS location, d.date AS date, d.source AS source ORDER BY d.date DESC LIMIT 10"
    )
    return {"gdacs_alerts": alerts, "fema_disasters": disasters}


@router.get("/disasters/by-state/{state}")
def disasters_by_state(state: str):
    results = run_cypher(
        "MATCH (d:Disaster)-[:OCCURRED_IN]->(l:Location {name: $state}) RETURN d",
        {"state": state.upper()},
    )
    return results


@router.get("/disasters/by-type/{incident_type}")
def disasters_by_type(incident_type: str):
    results = run_cypher(
        "MATCH (d:Disaster {type: $type}) RETURN d ORDER BY d.date DESC LIMIT 50",
        {"type": incident_type},
    )
    return results
