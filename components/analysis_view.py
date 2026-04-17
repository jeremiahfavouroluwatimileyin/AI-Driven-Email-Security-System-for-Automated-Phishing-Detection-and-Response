# Analysis view: renders the full analysis result panel for a selected email
# Handles routine, critical, phishing, and spam outcomes

import streamlit as st
import json
from datetime import datetime
import config


RISK_COLORS = {"low": "#4CAF50", "medium": "#FF9800", "high": "#F44336"}
PRIORITY_COLORS = {"low": "#78909C", "normal": "#42A5F5", "high": "#FF9800", "urgent": "#F44336"}
THREAT_COLORS = {"medium": "#FF9800", "high": "#F44336", "critical": "#B71C1C"}


def render_analysis(email: dict, result: dict):
    """Master render function. Routes to the correct view based on classification."""

    classification = result["decision"]["classification"]

    # Common email header shown for all types
    _render_email_header(email)

    st.divider()

    if classification == "phishing":
        _render_phishing_view(email, result)
    elif classification == "spam":
        _render_spam_view(email, result)
    elif classification == "critical":
        _render_critical_view(email, result)
    else:
        _render_routine_view(email, result)


def _render_email_header(email: dict):
    """Render the original email header info."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {email.get('subject', '(No Subject)')}")
        st.markdown(f"**From:** {email.get('from_name', 'Unknown')} `{email.get('from_email', '')}`")
    with col2:
        date = email.get("date", "")[:16].replace("T", " ")
        st.markdown(f"<div style='text-align:right; color:#888; padding-top:8px;'>{date}</div>", unsafe_allow_html=True)


def _render_routine_view(email: dict, result: dict):
    """Render view for routine emails: risk summary, key points, and auto-reply editor."""

    decision = result["decision"]
    analysis = result["analysis"]
    response = result.get("response", {})

    # Risk and priority badges
    col1, col2, col3 = st.columns(3)

    risk_level = decision.get("risk_level", "low")
    priority = decision.get("priority", "normal")
    risk_score = decision.get("risk_score", 0)

    with col1:
        rc = RISK_COLORS.get(risk_level, "#999")
        st.markdown(f"""
        <div style='background:{rc}22; border:1px solid {rc}; border-radius:8px; padding:12px; text-align:center;'>
            <div style='color:{rc}; font-size:1.4rem; font-weight:700;'>{risk_score}/100</div>
            <div style='color:#aaa; font-size:0.8rem;'>Risk Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        pc = PRIORITY_COLORS.get(priority, "#999")
        st.markdown(f"""
        <div style='background:{pc}22; border:1px solid {pc}; border-radius:8px; padding:12px; text-align:center;'>
            <div style='color:{pc}; font-size:1.1rem; font-weight:600;'>{priority.upper()}</div>
            <div style='color:#aaa; font-size:0.8rem;'>Priority</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        tone = analysis.get("tone", "neutral")
        st.markdown(f"""
        <div style='background:#1a2332; border:1px solid #333; border-radius:8px; padding:12px; text-align:center;'>
            <div style='color:#E0E0E0; font-size:1.1rem; font-weight:600;'>{tone.title()}</div>
            <div style='color:#aaa; font-size:0.8rem;'>Tone</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Collapsible key points section
    key_points = decision.get("key_points", {})
    with st.expander("📋 Key Points Extracted", expanded=True):
        kp_items = [
            ("Urgency", key_points.get("urgency")),
            ("Deadline", key_points.get("deadline")),
            ("Action Required", key_points.get("action_required")),
            ("Sender Role", key_points.get("sender_role")),
            ("Financial Amount", key_points.get("financial_amount")),
        ]

        for label, value in kp_items:
            if value:
                st.markdown(f"**{label}:** {value}")

        st.markdown(f"**Intent:** {analysis.get('intent', 'N/A')}")
        st.markdown(f"**Summary:** {analysis.get('summary', 'N/A')}")

    # Score breakdown
    with st.expander("📊 Risk Score Breakdown", expanded=False):
        breakdown = decision.get("score_breakdown", {})
        for dimension, score in breakdown.items():
            label = dimension.replace("_", " ").title()
            # Colour bar: green if score < 15, orange if 15-20, red if 20+
            bar_color = "#4CAF50" if score < 15 else ("#FF9800" if score < 20 else "#F44336")
            st.markdown(f"**{label}**: {score}/25")
            st.markdown(f"""
            <div style='background:#333; border-radius:4px; height:6px; margin-bottom:10px;'>
                <div style='background:{bar_color}; width:{int(score/25*100)}%; height:6px; border-radius:4px;'></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"*Reasoning: {decision.get('reasoning', 'N/A')}*")

    st.divider()

    # Auto-generated response editor
    st.markdown("#### ✍️ Automated Response Generated")
    st.caption("You can edit this response before sending or downloading.")

    if not response:
        st.info("Response not yet generated.")
        return

    edited_subject = st.text_input(
        "Subject",
        value=response.get("subject", ""),
        key=f"subject_edit_{email['id']}",
    )

    edited_body = st.text_area(
        "Body",
        value=response.get("body", ""),
        height=220,
        key=f"body_edit_{email['id']}",
    )

    col_dl, col_send, _ = st.columns([1, 1, 2])

    with col_dl:
        download_content = f"Subject: {edited_subject}\n\n{edited_body}"
        st.download_button(
            label="⬇️ Download",
            data=download_content,
            file_name=f"reply_{email['id']}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_send:
        if st.button("📤 Send Reply", use_container_width=True, key=f"send_{email['id']}"):
            st.success(f"Reply sent to {email.get('from_email', '')} ✓")
            st.balloons()


def _render_critical_view(email: dict, result: dict):
    """Render view for critical emails: delegation info and detailed report."""

    decision = result["decision"]
    delegation = result.get("delegation", {})

    # Critical warning banner
    st.markdown("""
    <div style='
        background: #FF980015;
        border: 1px solid #FF9800;
        border-left: 4px solid #FF9800;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 18px;
    '>
        <strong style='color: #FF9800; font-size: 1rem;'>⚠️ CRITICAL EMAIL DETECTED</strong><br>
        <span style='color: #ccc; font-size: 0.88rem;'>
            This email requires human attention and has been delegated accordingly.
        </span>
    </div>
    """, unsafe_allow_html=True)

    if delegation:
        dept = delegation.get("delegate_to_department", "Management")
        dept_email = delegation.get("delegate_to_email", "")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Delegated To:** {dept} Department")
            st.markdown(f"**Email:** `{dept_email}`")
        with col2:
            urgency = delegation.get("urgency", "high")
            uc = PRIORITY_COLORS.get(urgency, "#FF9800")
            st.markdown(f"**Urgency:** <span style='color:{uc}; font-weight:600;'>{urgency.upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**Escalation Subject:** {delegation.get('subject', 'N/A')}")

        st.divider()

        with st.expander("📋 Escalation Report", expanded=True):
            st.markdown(f"**Summary:** {delegation.get('summary', 'N/A')}")

            st.markdown("**Key Information:**")
            for item in delegation.get("key_information", []):
                st.markdown(f"- {item}")

            st.markdown(f"**Recommended Action:** {delegation.get('recommended_action', 'N/A')}")
            st.markdown(f"**Original Sender:** {delegation.get('original_sender', 'N/A')}")

        with st.expander("📊 Risk Assessment", expanded=False):
            st.markdown(f"**Risk Score:** {decision.get('risk_score', 0)}/100")
            st.markdown(f"**Reasoning:** {decision.get('reasoning', 'N/A')}")

        # Button to mark delegation as resolved
        if st.button("✅ Mark as Resolved", key=f"resolve_{email['id']}"):
            from utils.state import mark_delegation_resolved
            mark_delegation_resolved(1)
            st.success("Delegation marked as resolved.")


def _render_phishing_view(email: dict, result: dict):
    """Render view for phishing emails: red alert banner, red flags, threat details."""

    phishing = result.get("phishing_report", {})
    threat_level = phishing.get("threat_level", "high")
    tc = THREAT_COLORS.get(threat_level, "#F44336")

    # Phishing alert banner
    st.markdown(f"""
    <div style='
        background: #F4433620;
        border: 2px solid #F44336;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 20px;
        text-align: center;
    '>
        <div style='font-size: 2rem;'>🚫</div>
        <div style='color: #F44336; font-size: 1.2rem; font-weight: 700; margin: 6px 0;'>
            PHISHING EMAIL BLOCKED
        </div>
        <div style='color: #aaa; font-size: 0.88rem;'>
            Threat Level: <strong style='color:{tc};'>{threat_level.upper()}</strong>
            &nbsp;|&nbsp; Attack Type: {phishing.get("attack_type", "Unknown").replace("_", " ").title()}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Red flags list
    st.markdown("#### 🚩 Red Flags Detected")

    red_flags = phishing.get("red_flags", [])
    if red_flags:
        for flag in red_flags:
            st.markdown(f"""
            <div style='
                background: #F4433610;
                border-left: 3px solid #F44336;
                border-radius: 4px;
                padding: 8px 14px;
                margin-bottom: 6px;
                color: #E0E0E0;
                font-size: 0.88rem;
            '>⚠️ {flag}</div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No specific red flags extracted.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Security recommendation
    st.info(f"🔐 **Recommendation:** {phishing.get('recommendation', 'Do not interact with this email.')}")

    # Show the blocked email content collapsed for reference
    with st.expander("📧 View Blocked Email (Read Only)", expanded=False):
        st.markdown(f"**From:** {email.get('from_name')} `{email.get('from_email')}`")
        st.markdown(f"**Subject:** {email.get('subject')}")
        st.text(email.get("body", "")[:1000] + "..." if len(email.get("body", "")) > 1000 else email.get("body", ""))


def _render_spam_view(email: dict, result: dict):
    """Render view for spam emails: simple notice and move-to-spam confirmation."""

    st.markdown("""
    <div style='
        background: #9E9E9E15;
        border: 1px solid #9E9E9E;
        border-left: 4px solid #9E9E9E;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 18px;
    '>
        <strong style='color: #BDBDBD; font-size: 1rem;'>📪 SPAM DETECTED</strong><br>
        <span style='color: #aaa; font-size: 0.88rem;'>
            This email has been classified as spam and filtered automatically.
        </span>
    </div>
    """, unsafe_allow_html=True)

    analysis = result.get("analysis", {})
    st.markdown(f"**Intent:** {analysis.get('intent', 'N/A')}")
    st.markdown(f"**Summary:** {analysis.get('summary', 'N/A')}")

    with st.expander("📧 View Email", expanded=False):
        st.text(email.get("body", ""))
