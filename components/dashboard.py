# Dashboard component: shows aggregated stats and processing history

import streamlit as st


def render_dashboard():
    """Render the full statistics dashboard page."""

    st.markdown("## 📊 System Dashboard")
    st.caption("Overview of all emails processed by Wizard in this session.")

    stats = st.session_state.stats

    # Summary metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Processed", stats["total"])
    with col2:
        st.metric("Routine", stats["routine"], delta=None)
    with col3:
        st.metric("Critical", stats["critical"])
    with col4:
        st.metric("Phishing", stats["phishing"])
    with col5:
        st.metric("Spam", stats["spam"])

    st.divider()

    # Delegation tracking
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 📤 Delegation Status")
        st.metric("Total Delegated", stats["delegated"])
        if stats["pending_delegation"] > 0:
            st.warning(f"⏳ **{stats['pending_delegation']} pending** — awaiting human resolution")
        else:
            st.success("✅ No pending delegations")

    with col_b:
        st.markdown("### 🛡️ Threat Summary")
        if stats["total"] > 0:
            threat_rate = round((stats["phishing"] + stats["spam"]) / stats["total"] * 100, 1)
            phishing_rate = round(stats["phishing"] / stats["total"] * 100, 1)
            st.metric("Threat Rate", f"{threat_rate}%")
            st.metric("Phishing Rate", f"{phishing_rate}%")
        else:
            st.info("No emails processed yet.")

    st.divider()

    # Classification breakdown visual
    st.markdown("### 📈 Classification Breakdown")

    if stats["total"] == 0:
        st.info("No emails processed yet. Analyse some emails to see stats here.")
        return

    # Simple bar using Streamlit progress bars as a visual proxy
    categories = [
        ("Routine", stats["routine"], "#2196F3"),
        ("Critical", stats["critical"], "#FF9800"),
        ("Phishing", stats["phishing"], "#F44336"),
        ("Spam", stats["spam"], "#9E9E9E"),
    ]

    for name, count, color in categories:
        pct = count / stats["total"] if stats["total"] > 0 else 0
        pct_display = round(pct * 100, 1)

        st.markdown(f"""
        <div style='margin-bottom: 12px;'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
                <span style='color: #E0E0E0; font-size: 0.88rem;'>{name}</span>
                <span style='color: #888; font-size: 0.82rem;'>{count} ({pct_display}%)</span>
            </div>
            <div style='background: #333; border-radius: 6px; height: 10px;'>
                <div style='background: {color}; width: {pct_display}%; height: 10px; border-radius: 6px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Recent analysis history
    st.divider()
    st.markdown("### 🕑 Recent Analysis History")

    analysis_results = st.session_state.analysis_results
    emails = {e["id"]: e for e in st.session_state.emails}

    if not analysis_results:
        st.info("No analyses run yet.")
        return

    history_rows = []
    for email_id, result in analysis_results.items():
        email = emails.get(email_id, {})
        history_rows.append({
            "Subject": email.get("subject", "Unknown")[:50],
            "From": email.get("from_name", "Unknown"),
            "Classification": result["decision"]["classification"].upper(),
            "Risk Score": result["decision"]["risk_score"],
            "Priority": result["decision"]["priority"].upper(),
        })

    # Show as a simple styled table
    for row in reversed(history_rows):
        cls = row["Classification"].lower()
        cls_colors = {
            "routine": "#2196F3",
            "critical": "#FF9800",
            "phishing": "#F44336",
            "spam": "#9E9E9E",
        }
        color = cls_colors.get(cls, "#888")

        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.markdown(f"<span style='color:#E0E0E0; font-size:0.85rem;'>{row['Subject']}</span>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#888; font-size:0.82rem;'>{row['From']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:{color}; font-size:0.82rem; font-weight:600;'>{row['Classification']}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<span style='color:#888; font-size:0.82rem;'>{row['Risk Score']}/100</span>", unsafe_allow_html=True)
