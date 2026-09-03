import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def create_disaster_node(data: dict):
    with driver.session() as session:
        session.run(
            """
            MERGE (d:Disaster {id: $id})
            SET d.type = $type,
                d.title = $title,
                d.state = $state,
                d.date = $date,
                d.close_date = $close_date,
                d.source = $source
            MERGE (l:Location {name: $state})
            MERGE (d)-[:OCCURRED_IN]->(l)
            """,
            **data,
        )


def create_alert_node(data: dict):
    with driver.session() as session:
        session.run(
            """
            MERGE (a:Alert {id: $id})
            SET a.type = $type,
                a.name = $name,
                a.severity = $severity,
                a.country = $country,
                a.lat = $lat,
                a.lon = $lon,
                a.date = $date,
                a.source = $source
            MERGE (l:Location {name: $country})
            MERGE (a)-[:LOCATED_IN]->(l)
            """,
            **data,
        )


def run_cypher(query: str, params: dict = {}):
    with driver.session() as session:
        result = session.run(query, **params)
        return [record.data() for record in result]
