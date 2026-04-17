# Manages Streamlit session state across the application

import streamlit as st


def init_state():
    """Initialise all session state variables if they don't exist yet."""

    # Currently selected mode: 'demo' or 'real'
    if "mode" not in st.session_state:
        st.session_state.mode = "demo"

    # Currently active page: 'inbox', 'dashboard', 'manual'
    if "page" not in st.session_state:
        st.session_state.page = "inbox"

    # List of emails currently displayed in the inbox
    if "emails" not in st.session_state:
        st.session_state.emails = []

    # Dict mapping email id -> analysis result dict
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = {}

    # Which email is currently open/expanded
    if "selected_email_id" not in st.session_state:
        st.session_state.selected_email_id = None

    # Dashboard counters
    if "stats" not in st.session_state:
        st.session_state.stats = {
            "routine": 0,
            "critical": 0,
            "phishing": 0,
            "spam": 0,
            "delegated": 0,
            "pending_delegation": 0,
            "total": 0,
        }

    # Gmail OAuth credentials object
    if "gmail_credentials" not in st.session_state:
        st.session_state.gmail_credentials = None

    # Whether Gmail is currently connected
    if "gmail_connected" not in st.session_state:
        st.session_state.gmail_connected = False


def update_stats(classification: str, delegated: bool = False):
    """Increment the appropriate dashboard counter after an email is analysed."""

    st.session_state.stats["total"] += 1

    if classification == "routine":
        st.session_state.stats["routine"] += 1

    elif classification == "critical":
        st.session_state.stats["critical"] += 1
        if delegated:
            st.session_state.stats["delegated"] += 1
            st.session_state.stats["pending_delegation"] += 1

    elif classification == "phishing":
        st.session_state.stats["phishing"] += 1

    elif classification == "spam":
        st.session_state.stats["spam"] += 1


def mark_delegation_resolved(count: int = 1):
    """Call this when a delegated email has been actioned by the human recipient."""
    st.session_state.stats["pending_delegation"] = max(
        0, st.session_state.stats["pending_delegation"] - count
    )
