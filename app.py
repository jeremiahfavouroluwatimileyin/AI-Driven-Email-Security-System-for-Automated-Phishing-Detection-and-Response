# PAPI - Professional AI-Powered Intelligence
# Main application entry point

import os
import json
import streamlit as st

# Page config must be first Streamlit call
st.set_page_config(
    page_title="PAPI - Email Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Internal imports after page config
from utils.state import init_state, update_stats
from components.sidebar import render_sidebar
from components.email_card import render_email_card, render_inbox_header
from components.analysis_view import render_analysis
from components.dashboard import render_dashboard
from agents.intelligent_agent import analyse as intelligent_analyse
from agents.decision_agent import evaluate as decision_evaluate
from agents.response_agent import (
    generate_auto_reply,
    generate_delegation_report,
    generate_phishing_report,
)
import utils.gmail_client as gmail_client
import config


# Custom CSS for dark theme polish
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0D1117; }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    /* Remove default padding on main block */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }

    /* Button tweaks */
    .stButton > button {
        border-radius: 8px;
        font-size: 0.85rem;
    }

    /* Text input and text area */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #161B22;
        border: 1px solid #30363D;
        color: #E0E0E0;
        border-radius: 8px;
    }

    /* Expander header */
    .streamlit-expanderHeader {
        background-color: #161B22;
        border-radius: 8px;
    }

    /* Metric value */
    [data-testid="metric-container"] { background: #161B22; border-radius: 10px; padding: 12px; }

    /* Divider */
    hr { border-color: #30363D; }
</style>
""", unsafe_allow_html=True)


def run_full_pipeline(email: dict) -> dict:
    """
    Run all three agents on an email and return the combined result dict.
    Also updates session state stats.
    """
    with st.spinner("🤖 Intelligent Agent: analysing content..."):
        analysis = intelligent_analyse(email)

    with st.spinner("⚖️ Decision Agent: evaluating risk..."):
        decision = decision_evaluate(email, analysis)

    classification = decision["classification"]
    result = {"analysis": analysis, "decision": decision}

    if classification == "routine":
        with st.spinner("✍️ Response Agent: generating reply..."):
            result["response"] = generate_auto_reply(email, decision)

    elif classification == "critical":
        with st.spinner("📤 Response Agent: preparing delegation report..."):
            result["delegation"] = generate_delegation_report(email, decision)

    elif classification == "phishing":
        with st.spinner("🚨 Response Agent: compiling threat report..."):
            result["phishing_report"] = generate_phishing_report(email, analysis)

    # Update dashboard counters
    update_stats(
        classification=classification,
        delegated=(classification == "critical"),
    )

    return result


def render_inbox(emails: list):
    """Render the inbox page: email list with inline analysis below each selected card."""

    render_inbox_header()
    st.caption(f"{len(emails)} email(s)")

    for email in emails:
        existing_result = st.session_state.analysis_results.get(email["id"])
        render_email_card(email, existing_result)

        # If this email is selected, render analysis directly below its card
        if st.session_state.selected_email_id == email["id"]:
            st.markdown("---")

            if existing_result:
                # Already analysed — show full result view inline
                render_analysis(email, existing_result)
            else:
                # Not yet analysed — show "ready to analyse" prompt inline
                st.markdown("### 🔍 Analysis")
                st.info(f"Ready to analyse: **{email.get('subject', '')}**")
                st.markdown(
                    f"**From:** {email.get('from_name')} `{email.get('from_email')}`"
                )
                st.caption(
                    "Use the Preview button on the email card to read the full body."
                )
                st.markdown("---")

                if st.button(
                    "🚀 Run PAPI Analysis",
                    type="primary",
                    use_container_width=True,
                    key=f"run_analysis_{email['id']}",
                ):
                    result = run_full_pipeline(email)
                    st.session_state.analysis_results[email["id"]] = result
                    st.rerun()

            st.markdown("---")


def render_manual_analysis():
    """Render the manual email input and analysis page."""

    st.markdown("## 🔍 Manual Email Analysis")
    st.caption("Enter email details manually for on-demand analysis.")

    with st.form("manual_form"):
        col1, col2 = st.columns(2)
        with col1:
            sender_name = st.text_input("Sender Name", placeholder="e.g. John Smith")
        with col2:
            sender_email = st.text_input("Sender Email", placeholder="e.g. john@company.com")

        subject = st.text_input("Subject", placeholder="Email subject line")
        body = st.text_area("Email Body", height=200, placeholder="Paste or type the email body here...")

        submitted = st.form_submit_button("🚀 Analyse Email", type="primary", use_container_width=True)

    if submitted:
        if not body.strip():
            st.warning("Please enter the email body before analysing.")
            return

        manual_email = {
            "id": f"manual_{hash(body[:50])}",
            "from_name": sender_name or "Unknown",
            "from_email": sender_email or "unknown@unknown.com",
            "subject": subject or "(No Subject)",
            "body": body,
            "date": "",
            "source": "manual",
        }

        st.divider()
        st.markdown("### Analysis Result")

        result = run_full_pipeline(manual_email)
        render_analysis(manual_email, result)


def render_gmail_connect():
    """Render the Gmail OAuth connection flow."""

    st.markdown("### 🔗 Connect Gmail Account")
    st.info(f"Connect **{config.USER_EMAIL}** to fetch live emails.")

    # Check for credentials: either the secrets dict or the local file will do
    has_secrets = "google_oauth" in st.secrets
    has_local_file = os.path.exists("client_secret.json")

    if not has_secrets and not has_local_file:
        st.error(
            "Google OAuth credentials not found. "
            "Add a `[google_oauth]` section to your Streamlit secrets, "
            "or place `client_secret.json` in the project root for local development."
        )
        st.markdown("[How to set up Streamlit secrets →](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)")
        st.markdown("[Google Cloud Console →](https://console.cloud.google.com/)")
        return

    if not st.session_state.gmail_connected:
        if st.button("🔑 Authorise with Google"):
            auth_url, flow = gmail_client.get_auth_url()
            st.session_state["_oauth_flow"] = flow
            st.markdown(f"**[Click here to authorise →]({auth_url})**")
            st.caption("After authorising, paste the code below.")

        code = st.text_input("Paste authorisation code here")
        if code and st.session_state.get("_oauth_flow"):
            try:
                creds = gmail_client.exchange_code_for_credentials(
                    st.session_state["_oauth_flow"], code.strip()
                )
                st.session_state.gmail_credentials = creds
                st.session_state.gmail_connected = True
                st.success("Gmail connected successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Authorisation failed: {e}")
    else:
        st.success(f"✅ Gmail connected: {config.USER_EMAIL}")
        if st.button("Disconnect"):
            st.session_state.gmail_credentials = None
            st.session_state.gmail_connected = False
            st.rerun()


def main():
    """Main app controller: initialises state, renders sidebar, routes to the correct page."""

    init_state()
    render_sidebar()

    page = st.session_state.page
    mode = st.session_state.mode

    if page == "dashboard":
        render_dashboard()
        return

    if page == "manual":
        render_manual_analysis()
        return

    # Inbox page: no extra heading here, render_inbox_header handles it inside render_inbox
    if mode == "demo":
        # Load demo emails from JSON if not already loaded for this mode
        if not st.session_state.emails or st.session_state.get("_last_mode") != "demo":
            with open("data/demo_emails.json") as f:
                st.session_state.emails = json.load(f)
            st.session_state["_last_mode"] = "demo"

        if not st.session_state.emails:
            st.info("No demo emails available.")
            return

        render_inbox(st.session_state.emails)

    else:
        # Real mode: Gmail OAuth integration
        render_gmail_connect()

        if st.session_state.gmail_connected:
            col_fetch, col_info = st.columns([1, 3])
            with col_fetch:
                if st.button("📬 Fetch Emails", type="primary"):
                    with st.spinner("Fetching emails from Gmail..."):
                        try:
                            emails = gmail_client.fetch_emails(st.session_state.gmail_credentials)
                            st.session_state.emails = emails
                            st.session_state["_last_mode"] = "real"
                            st.success(f"Fetched {len(emails)} emails.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to fetch emails: {e}")

            with col_info:
                st.caption(f"Fetching from: {config.USER_EMAIL} — up to {config.GMAIL_MAX_RESULTS} emails")

            if st.session_state.get("emails"):
                st.divider()
                render_inbox(st.session_state.emails)


if __name__ == "__main__":
    main()
