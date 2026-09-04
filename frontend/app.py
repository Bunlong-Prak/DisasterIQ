import os
import re
import streamlit as st
from neo4j import GraphDatabase
from groq import Groq
from gdacs.api import GDACSAPIReader
import httpx

st.set_page_config(page_title="DisasterIQ", layout="wide")

# Connections
@st.cache_resource
def get_neo4j():
    return GraphDatabase.driver(
        st.secrets["NEO4J_URI"],
        auth=(st.secrets["NEO4J_USER"], st.secrets["NEO4J_PASSWORD"])
    )

@st.cache_resource
def get_groq():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

def run_cypher(query, params={}):
    driver = get_neo4j()
    with driver.session() as session:
        result = session.run(query, **params)
        return [record.data() for record in result]

def ingest_gdacs():
    client = GDACSAPIReader()
    events = client.latest_events()
    features = events.features if hasattr(events, 'features') else events.get('features', [])
    driver = get_neo4j()
    count = 0
    with driver.session() as session:
        for event in features:
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
            session.run("""
                MERGE (a:Alert {id: $id})
                SET a.type=$type, a.name=$name, a.severity=$severity,
                    a.country=$country, a.lat=$lat, a.lon=$lon,
                    a.date=$date, a.source='GDACS'
                MERGE (l:Location {name: $country})
                MERGE (a)-[:LOCATED_IN]->(l)
            """,
                id=str(props.get("eventid", "")),
                type=props.get("eventtype", ""),
                name=props.get("name", ""),
                severity=props.get("alertlevel", ""),
                country=props.get("country", ""),
                lat=lat, lon=lon,
                date=str(props.get("fromdate", ""))
            )
            count += 1
    return count

def ingest_fema():
    resp = httpx.get(
        "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries",
        params={"$top": 50, "$orderby": "declarationDate desc"},
        timeout=30,
    )
    records = resp.json().get("DisasterDeclarationsSummaries", [])
    driver = get_neo4j()
    with driver.session() as session:
        for r in records:
            session.run("""
                MERGE (d:Disaster {id: $id})
                SET d.type=$type, d.title=$title, d.state=$state,
                    d.date=$date, d.source='FEMA'
                MERGE (l:Location {name: $state})
                MERGE (d)-[:OCCURRED_IN]->(l)
            """,
                id=str(r.get("disasterNumber", "")),
                type=r.get("incidentType", ""),
                title=r.get("declarationTitle", ""),
                state=r.get("state", ""),
                date=str(r.get("declarationDate", ""))
            )
    return len(records)

SCHEMA = """
Nodes:
- Disaster(id, type, title, state, date, source)
  - type examples: 'Fire', 'Flood', 'Tropical Storm', 'Severe Storm'
  - state examples: 'TX', 'CA', 'FL', 'IN', 'AK' (US state abbreviations)
  - date format: '2026-08-25T00:00:00.000Z'
  - source: 'FEMA'
- Alert(id, type, name, severity, country, lat, lon, date, source)
  - type examples: 'EQ' (earthquake), 'TC' (tropical cyclone), 'FL' (flood)
  - severity examples: 'Green', 'Orange', 'Red'
  - country examples: 'United States', 'Japan', 'Mexico'
  - source: 'GDACS'
- Location(name) — connected to both Disaster and Alert nodes

Relationships:
- (Disaster)-[:OCCURRED_IN]->(Location) where Location.name = US state abbreviation
- (Alert)-[:LOCATED_IN]->(Location) where Location.name = country name
"""

MODEL = "openai/gpt-oss-20b"

def clean_cypher(raw: str) -> str:
    # Remove <think>...</think> blocks (reasoning models)
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    # Remove markdown code fences
    cleaned = re.sub(r"```(?:cypher)?", "", cleaned)
    return cleaned.strip()

def ask(question):
    client = get_groq()
    system_prompt = (
        "You are a Neo4j Cypher expert. "
        "Given a schema and a question, write a valid Cypher query to answer it. "
        "Return ONLY the Cypher query — no markdown, no explanation, no code fences, no thinking. "
        "The query must start with MATCH, RETURN, or WITH."
    )
    try:
        cypher_resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Schema:\n{SCHEMA}\n\nQuestion: {question}\n\nCypher query:"}
            ],
            temperature=0,
        )
        raw = cypher_resp.choices[0].message.content.strip()
        cypher = clean_cypher(raw)
    except Exception as e:
        return f"Groq error: {str(e)}", "", []

    try:
        data = run_cypher(cypher)
    except Exception as e:
        return f"Cypher error: {str(e)}", cypher, []

    try:
        answer_resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Answer the user's question clearly and concisely based on the data provided. If data is empty, say no results were found."},
                {"role": "user", "content": f"Question: {question}\nData from database: {str(data[:10])}"}
            ],
            temperature=0,
        )
        answer = re.sub(r"<think>.*?</think>", "", answer_resp.choices[0].message.content, flags=re.DOTALL).strip()
        return answer, cypher, data
    except Exception as e:
        return str(data), cypher, data


# UI
st.title("DisasterIQ")
st.caption("Disaster intelligence platform, Knowledge Graph + natural language queries")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Refresh Data", type="primary"):
        with st.spinner("Ingesting..."):
            g = ingest_gdacs()
            f = ingest_fema()
            st.success(f"Loaded {g} GDACS alerts + {f} FEMA disasters")

tab1, tab2 = st.tabs(["Live Data", "Query"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("GDACS Alerts")
        alerts = run_cypher(
            "MATCH (a:Alert) RETURN a.name AS name, a.type AS type, a.severity AS severity, a.country AS country, a.date AS date ORDER BY a.date DESC LIMIT 15"
        )
        if alerts:
            st.dataframe(alerts, use_container_width=True)
            map_data = run_cypher("MATCH (a:Alert) WHERE a.lat IS NOT NULL RETURN a.lat AS latitude, a.lon AS longitude, a.name AS name LIMIT 50")
            if map_data:
                st.map(map_data)
        else:
            st.info("No alerts yet. Click Refresh Data.")

    with col_b:
        st.subheader("FEMA Disasters")
        disasters = run_cypher(
            "MATCH (d:Disaster) RETURN d.title AS title, d.type AS type, d.state AS state, d.date AS date ORDER BY d.date DESC LIMIT 15"
        )
        if disasters:
            st.dataframe(disasters, use_container_width=True)
        else:
            st.info("No disasters yet. Click Refresh Data.")

with tab2:
    st.subheader("Query the disaster database")
    st.caption("Ask in plain English. The system generates a graph query and returns results.")
    question = st.text_input("Question", placeholder="What disasters hit Texas recently? Which countries had red alerts?")
    if question:
        with st.spinner("Running..."):
            answer, cypher, context = ask(question)
        st.markdown("### Result")
        st.write(answer)
        with st.expander("Query details"):
            st.code(cypher, language="cypher")
            st.json(context)
