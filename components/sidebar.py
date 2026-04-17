# Sidebar navigation component

import streamlit as st
from utils.state import init_state


def render_sidebar():
    """Render the Wizard sidebar with navigation and mode toggle."""

    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0;'>
            <h2 style='color: #4F8EF7; margin: 0; font-size: 2rem;'>🛡️ Wizard</h2>
            <p style='color: #888; font-size: 0.78rem; margin: 2px 0 0 0;'>
                Professional AI-Powered Intelligence
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Mode toggle
        st.markdown("**Mode**")
        mode = st.radio(
            label="Select mode",
            options=["Demo Mode", "Real Mode"],
            index=0 if st.session_state.mode == "demo" else 1,
            label_visibility="collapsed",
        )
        st.session_state.mode = "demo" if mode == "Demo Mode" else "real"

        st.divider()

        # Navigation
        st.markdown("**Navigation**")

        pages = {
            "📥  Inbox": "inbox",
            "📊  Dashboard": "dashboard",
            "🔍  Manual Analysis": "manual",
        }

        for label, page_key in pages.items():
            is_active = st.session_state.page == page_key
            if st.button(
                label,
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"nav_{page_key}",
            ):
                st.session_state.page = page_key
                st.session_state.selected_email_id = None
                st.rerun()

        st.divider()

        # Quick stats in sidebar
        stats = st.session_state.stats
        st.markdown("**Quick Stats**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", stats["total"])
            st.metric("Phishing", stats["phishing"])
        with col2:
            st.metric("Routine", stats["routine"])
            st.metric("Critical", stats["critical"])

        if stats["pending_delegation"] > 0:
            st.warning(f"⏳ {stats['pending_delegation']} pending delegation(s)")

        st.divider()

        # User info at bottom
        st.markdown(f"""
        <div style='font-size: 0.8rem; color: #888; text-align: center;'>
            <strong>Jeremiah Favour</strong><br>
            Tech Solutions
        </div>
        """, unsafe_allow_html=True)
