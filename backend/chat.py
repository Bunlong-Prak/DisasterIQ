import os
from dotenv import load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from graph import run_cypher

load_dotenv()

router = APIRouter()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCHEMA = """
Nodes:
- Disaster {id, type, title, state, date, close_date, source}
- Alert {id, type, name, severity, country, lat, lon, date, source}
- Location {name}

Relationships:
- (Disaster)-[:OCCURRED_IN]->(Location)
- (Alert)-[:LOCATED_IN]->(Location)
"""

CYPHER_PROMPT = """You are a Neo4j Cypher expert. Given the schema below and a user question, write a Cypher query to answer it.
Return ONLY the Cypher query, no explanation, no markdown.

Schema:
{schema}

Question: {question}
Cypher:"""

ANSWER_PROMPT = """Given a user question and the data returned from a Neo4j database, write a clear and concise answer.

Question: {question}
Data: {data}
Answer:"""


class ChatRequest(BaseModel):
    question: str


@router.post("/")
def chat(req: ChatRequest):
    # Step 1: LLM generates Cypher from question (XAI: we expose this)
    cypher_response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "user", "content": CYPHER_PROMPT.format(
                schema=SCHEMA,
                question=req.question
            )}
        ],
        temperature=0,
    )
    cypher_query = cypher_response.choices[0].message.content.strip()

    # Step 2: Run Cypher against Neo4j
    try:
        results = run_cypher(cypher_query)
    except Exception as e:
        return {
            "answer": f"Could not run query: {str(e)}",
            "cypher_query": cypher_query,
            "context": [],
        }

    # Step 3: LLM formats results into natural language
    answer_response = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "user", "content": ANSWER_PROMPT.format(
                question=req.question,
                data=str(results)
            )}
        ],
        temperature=0,
    )
    answer = answer_response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "cypher_query": cypher_query,  # XAI: show what query was generated
        "context": results,            # XAI: show raw graph data used
    }
