# DisasterIQ Build Plan

## Phase 1 — Data Pipeline (Day 1-2)
- [ ] Set up Neo4j AuraDB free account
- [ ] Set up Groq API free account
- [ ] Test FEMA OpenFEMA API (no key needed)
- [ ] Test GDACS API via gdacs-api pip package
- [ ] Get data flowing into Neo4j (disaster nodes, alert nodes, location nodes)

## Phase 2 — LLM Chat (Day 3-4)
- [ ] Wire LangChain GraphCypherQAChain to Neo4j
- [ ] Test natural language queries against graph
- [ ] Verify XAI output (show Cypher query used)

## Phase 3 — Frontend (Day 5)
- [ ] Streamlit dashboard: live alerts table + map
- [ ] Streamlit chat tab: question input + answer + XAI expander

## Phase 4 — Polish + Deploy (Day 6-7)
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Streamlit Cloud (free)
- [ ] Write README with demo GIF
- [ ] Push to GitHub — link in application

## Accounts Needed (all free)
- Neo4j AuraDB: https://neo4j.com/cloud/platform/aura-graph-database/
- Groq: https://console.groq.com
- Railway: https://railway.app
- Streamlit Cloud: https://streamlit.io/cloud
- Supabase: https://supabase.com (if needed)

## Why This Impresses Dr. Dogdu
Covers 4 of the 7 core job responsibilities:
1. Knowledge graph data model (Neo4j)
2. LLM-based conversational interface (Groq + LangChain)
3. Real-time alert system (GDACS polling)
4. Explainable AI output (show Cypher reasoning)
Plus uses two of the exact preferred qualifications: graph databases and LLMs/NLP.
