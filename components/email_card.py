# Email card component: renders a single email preview in the inbox list

import streamlit as st
from datetime import datetime


# Map classification to badge colour
CLASSIFICATION_COLORS = {
    "routine": "#2196F3",
    "critical": "#FF9800",
    "phishing": "#F44336",
    "spam": "#9E9E9E",
    "pending": "#607D8B",
}

CLASSIFICATION_ICONS = {
    "routine": "✅",
    "critical": "⚠️",
    "phishing": "🚫",
    "spam": "📪",
    "pending": "⏳",
}


def _format_date(date_str: str) -> str:
    """Convert ISO date string to a friendly format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b, %H:%M")
    except Exception:
        return date_str[:16] if date_str else ""


def render_inbox_header():
    """
    Render the centred inbox header at the top of the inbox page.
    Call this once before looping over email cards.
    """
    st.markdown("""
    <div style='text-align: center; padding: 18px 0 24px 0;'>
        <h1 style='color: #E0E0E0; font-size: 1.8rem; margin: 0;'>🛡️ PAPI Inbox</h1>
        <p style='color: #888; font-size: 0.82rem; margin: 4px 0 0 0;'>
            AI-powered email intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_email_card(email: dict, analysis_result: dict = None):
    """
    Render a single email as a clickable card in the inbox list.

    The card shows:
      - "From: NAME <email>" all bold and white on one line
      - Subject line bold and white, body snippet in light grey
      - Date and classification badge top-right
      - Analyse and Preview buttons right-aligned on the same row
      - If Preview is toggled, the full body appears directly below
        the card (inside the left column), with a close toggle on the button

    analysis_result is None if the email has not been analysed yet.
    """

    email_id = email["id"]
    is_selected = st.session_state.selected_email_id == email_id

    # Build classification badge HTML if the email has been analysed
    if analysis_result:
        classification = analysis_result["decision"]["classification"]
        badge_color = CLASSIFICATION_COLORS.get(classification, "#607D8B")
        badge_icon = CLASSIFICATION_ICONS.get(classification, "📧")
        badge_html = (
            f'<span style="'
            f'background: {badge_color}; '
            f'color: white; '
            f'padding: 2px 9px; '
            f'border-radius: 12px; '
            f'font-size: 0.72rem;">'
            f'{badge_icon} {classification.upper()}</span>'
        )
    else:
        badge_html = "<span style=\"color: #E0E0E0; font-size: 0.75rem;\">Not analysed</span>"

    # Highlight the selected card with a blue border
    border_style = "2px solid #4F8EF7" if is_selected else "1px solid #333"
    bg_color = "#1a2332" if is_selected else "#161B22"

    subject_preview = email.get("subject", "(No Subject)")[:60]
    body_preview = email.get("body", "")[:90].replace("\n", " ") + "..."
    date_str = _format_date(email.get("date", ""))

    from_name = email.get("from_name", "Unknown")
    from_email = email.get("from_email", "")

    # Card HTML: "From: NAME <email>" all bold and white on one line
    st.markdown(f"""
    <div style='
        background: {bg_color};
        border: {border_style};
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 6px;
    '>
        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
            <div style='flex: 1;'>
                <div style='font-size: 0.88rem; color: #FFFFFF; margin-bottom: 4px;'>
                    <strong>From: {from_name} &lt;{from_email}&gt;</strong>
                </div>
                <div style='font-size: 0.88rem; color: #FFFFFF; margin: 3px 0;'>
                    <strong>{subject_preview}</strong>
                </div>
                <div style='font-size: 0.78rem; color: #CCCCCC; margin-top: 3px;'>
                    {body_preview}
                </div>
            </div>
            <div style='text-align: right; min-width: 110px; margin-left: 12px;'>
                <div style='font-size: 0.75rem; color: #AAAAAA; margin-bottom: 6px;'>{date_str}</div>
                {badge_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Analyse and Preview on the same line, pushed right with a spacer column
    _, col_analyse, col_preview = st.columns([3, 1, 1])

    with col_analyse:
        if st.button(
            "🔍 Analyse" if not analysis_result else "📄 Result",
            key=f"analyse_{email_id}",
            use_container_width=True,
        ):
            # Open the right-side analysis panel and close any open preview
            st.session_state.selected_email_id = email_id
            st.session_state[f"preview_open_{email_id}"] = False
            st.rerun()

    with col_preview:
        # The button label toggles so it acts as both open and close
        preview_is_open = st.session_state.get(f"preview_open_{email_id}", False)
        if st.button(
            "✖ Close" if preview_is_open else "👁 Preview",
            key=f"preview_{email_id}",
            use_container_width=True,
        ):
            st.session_state[f"preview_open_{email_id}"] = not preview_is_open
            st.rerun()

    # Preview panel rendered directly below this card when toggled on.
    # It stays inside the left inbox column and never touches the right panel.
    if st.session_state.get(f"preview_open_{email_id}", False):
        # Escape any HTML characters in the body before injecting into HTML
        safe_body = (
            email.get("body", "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        st.markdown(f"""
        <div style='
            background: #0D1117;
            border: 1px solid #30363D;
            border-top: 3px solid #4F8EF7;
            border-radius: 0 0 8px 8px;
            padding: 16px;
            margin-top: -4px;
            margin-bottom: 12px;
            color: #E0E0E0;
            font-size: 0.85rem;
            white-space: pre-wrap;
            line-height: 1.6;
            font-family: monospace;
        '>{safe_body}</div>
        """, unsafe_allow_html=True)
