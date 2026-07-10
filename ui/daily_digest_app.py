import sys
import io

# Force UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# Ensure DB path resolves correctly regardless of run location
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "outcome_log.db")

st.set_page_config(
    page_title="Jobline Pipeline",
    page_icon="\ud83c\udfaf",
    layout="wide"
)

def load_jobs(verdict_filter=None, min_score=0):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, date_found, platform, company, role,
               job_url, match_score, verdict, outcome, jd_text
        FROM applications
        WHERE match_score >= ?
    """
    params = [min_score]
    if verdict_filter and verdict_filter != "All":
        query += " AND verdict = ?"
        params.append(verdict_filter)
    query += " ORDER BY match_score DESC NULLS LAST"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def update_outcome(job_id: int, outcome: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE applications SET outcome = ? WHERE id = ?",
        (outcome, job_id)
    )
    conn.commit()
    conn.close()

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("Jobline Pipeline")
st.sidebar.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %H:%M')}")

verdict_options = ["All", "Strong Match", "Good Fit", "Partial Fit", "DISQUALIFIED", "BLACKLISTED"]
selected_verdict = st.sidebar.selectbox("Filter by Verdict", verdict_options, index=0)
min_score = st.sidebar.slider("Minimum Match Score", 0, 100, 40)
show_jd = st.sidebar.checkbox("Show full JD text", value=False)

if st.sidebar.button("Refresh Data"):
    st.rerun()

# ── Main ───────────────────────────────────────────────────────────────────
st.title("Daily Job Digest")

df = load_jobs(
    verdict_filter=selected_verdict if selected_verdict != "All" else None,
    min_score=min_score
)

# ── Metrics row ────────────────────────────────────────────────────────────
total      = len(df)
strong     = len(df[df["verdict"] == "Strong Match"])
good       = len(df[df["verdict"] == "Good Fit"])
applied    = len(df[df["outcome"] == "applied"])
disq       = len(df[df["verdict"] == "DISQUALIFIED"])

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Jobs",      total)
col2.metric("Strong Matches",  strong,  delta="Priority")
col3.metric("Good Fits",       good)
col4.metric("Applied",         applied)
col5.metric("Disqualified",    disq,    delta="Auto-filtered")

st.divider()

# ── Job cards ──────────────────────────────────────────────────────────────
qualified_df = df[~df["verdict"].isin(["DISQUALIFIED", "BLACKLISTED"])].copy()

if qualified_df.empty:
    st.warning("No qualified jobs found. Run the scraper and evaluator first.")
    st.stop()

for _, row in qualified_df.iterrows():
    score = row["match_score"] if pd.notna(row["match_score"]) else 0
    verdict = row["verdict"] or "Pending"

    # Card color by verdict
    color_map = {
        "Strong Match": "\ud83d\udfe2",
        "Good Fit":     "\ud83d\udd35",
        "Partial Fit":  "\ud83d\udfe1",
        "BLACKLISTED":  "\u26d4",
        "Pending":      "\u26aa",
    }
    icon = color_map.get(verdict, "\u26aa")

    with st.expander(
        f"{icon} **{row['role']}** @ {row['company']}  "
        f"| Score: `{int(score) if score else 'N/A'}`  "
        f"| {verdict}  "
        f"| {row['platform']}"
    ):
        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.markdown(f"**Found:** {row['date_found']}")
            st.markdown(f"**URL:** [{row['job_url']}]({row['job_url']})")
            if show_jd and row["jd_text"]:
                st.markdown("**JD Preview:**")
                st.caption(str(row["jd_text"])[:800] + "...")

        with col_b:
            st.markdown("**Update Outcome:**")
            new_outcome = st.selectbox(
                "Status",
                ["pending", "applied", "no_response", "rejected", "interview"],
                index=["pending", "applied", "no_response",
                       "rejected", "interview"].index(
                    row["outcome"] if row["outcome"] in
                    ["pending", "applied", "no_response", "rejected", "interview"]
                    else "pending"
                ),
                key=f"outcome_{row['id']}"
            )
            if st.button("Save", key=f"save_{row['id']}"):
                update_outcome(int(row["id"]), new_outcome)
                st.success("Updated.")
                st.rerun()

st.divider()

# ── Outcome log summary ────────────────────────────────────────────────────
st.subheader("Outcome Log")
outcome_counts = df.groupby("outcome").size().reset_index(name="count")
if not outcome_counts.empty:
    st.dataframe(outcome_counts, use_container_width=True, hide_index=True)
else:
    st.caption("No outcomes logged yet.")
