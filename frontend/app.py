import streamlit as st
import httpx
import pandas as pd

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="DisasterIQ", page_icon="🚨", layout="wide")
st.title("DisasterIQ — AI Disaster Intelligence Platform")

tab1, tab2 = st.tabs(["Live Alerts", "Ask the AI"])

with tab1:
    st.subheader("Recent Global Alerts")
    try:
        resp = httpx.get(f"{API_BASE}/alerts/recent", timeout=10)
        alerts = resp.json()
        if alerts:
            df = pd.DataFrame([a["a"] for a in alerts])
            st.dataframe(df, use_container_width=True)
            # Map if lat/lon available
            map_df = df.dropna(subset=["lat", "lon"])
            if not map_df.empty:
                st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}))
        else:
            st.info("No alerts loaded yet. Data ingestion runs on startup.")
    except Exception as e:
        st.error(f"Could not reach API: {e}")

with tab2:
    st.subheader("Ask About Disasters")
    st.caption("Powered by Groq LLaMA3 + Neo4j Knowledge Graph")

    question = st.text_input(
        "Ask a question",
        placeholder="What disasters hit Texas in the last year? Which countries had the most red alerts?",
    )

    if question:
        with st.spinner("Thinking..."):
            try:
                resp = httpx.post(
                    f"{API_BASE}/chat/",
                    json={"question": question},
                    timeout=30,
                )
                data = resp.json()
                st.markdown("### Answer")
                st.write(data["answer"])

                with st.expander("How it reasoned (XAI)"):
                    st.code(data.get("cypher_query", ""), language="cypher")
                    st.json(data.get("context", []))
            except Exception as e:
                st.error(f"Error: {e}")
