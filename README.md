# DisasterIQ — AI Disaster Intelligence Platform

AI-driven disaster and emergency management platform built for ASU CS Research Assistant application.

## What It Does

- Ingests live disaster data from FEMA OpenFEMA API and GDACS (Global Disaster Alert and Coordination System)
- Builds a knowledge graph in Neo4j: disasters, locations, agencies, alerts, resources as interconnected nodes
- LLM chat interface (Groq + LangChain + Neo4j) for natural language queries against the knowledge graph
- Real-time alert polling: GDACS updates every 6 minutes, dashboard shows new events
- Explainable outputs: each AI answer shows which graph nodes and relationships it used

## Stack

| Layer | Tool |
|-------|------|
| Backend | FastAPI (Python) |
| Knowledge Graph | Neo4j AuraDB (free tier) |
| LLM | Groq API (free, llama3) |
| LLM Orchestration | LangChain + Neo4j integration |
| Regular DB | Supabase (PostgreSQL) |
| Frontend | Streamlit (free hosting) |
| Data Sources | FEMA OpenFEMA API, GDACS API, USGS Earthquake API |

## Data Sources (all free, no key required)

- FEMA OpenFEMA: https://www.fema.gov/api/open
- GDACS: https://www.gdacs.org/feed_reference.aspx (gdacs-api pip package)
- USGS Earthquakes: https://earthquake.usgs.gov/fdsnws/event/1/
- ReliefWeb: https://apidoc.reliefweb.int/

## Open Source Bases

- neo4j-labs/llm-graph-builder — knowledge graph construction backbone
- LangChain Neo4j integration — LLM + graph querying
- gdacs-api — GDACS data ingestion

## Related Research Position

ASU Computer Science — Research Assistant, AI Driven Disaster and Emergency Management System
Supervisor: Dr. Erdogan Dogdu (erdogan.dogdu@angelo.edu)
