def get_css() -> str:
    theme = st.session_state.get("theme", "dark")

    if theme == "dark":
        bg = "#0F172A"
        bg_secondary = "#1E293B"
        text_primary = "#F1F5F9"
        text_secondary = "#94A3B8"
        border = "#334155"
        card_bg = "#1E293B"
        input_bg = "#1E293B"
        input_text = "#F1F5F9"
        placeholder_text = "#94A3B8"
        button_bg = "#1E293B"
        button_hover_bg = "#293548"
        assistant_bubble = "#1E293B"
        accent = "#3B82F6"
    else:
        bg = "#F8FAFC"
        bg_secondary = "#F1F5F9"
        text_primary = "#1E293B"
        text_secondary = "#64748B"
        border = "#CBD5E1"
        card_bg = "#FFFFFF"
        input_bg = "#FFFFFF"
        input_text = "#0F172A"
        placeholder_text = "#64748B"
        button_bg = "#FFFFFF"
        button_hover_bg = "#F1F5F9"
        assistant_bubble = "#FFFFFF"
        accent = "#2563EB"

    return textwrap.dedent(f"""
    <style>
    :root {{
        --bg: {bg}; 
        --bg-secondary: {bg_secondary}; 
        --text-primary: {text_primary};
        --text-secondary: {text_secondary}; 
        --border: {border}; 
        --card-bg: {card_bg};
        --button-bg: {button_bg}; 
        --button-hover-bg: {button_hover_bg};
        --assistant-bubble: {assistant_bubble}; 
        --accent: {accent};
        --input-bg: {input_bg}; 
        --input-text: {input_text}; 
        --placeholder-text: {placeholder_text};
    }}
    
    /* منع الفلاش الأبيض / Flash Fix عند إعادة التحميل */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: var(--bg) !important;
        color: var(--text-primary) !important;
    }}

    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
        "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;

    /* إصلاح لون الخطوط في كل أنواع عناصر النصوص (Dark & Light Mode) */
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] strong,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stChatMessageContent"] *,
    .stMarkdown, .stMarkdown p,
    h1, h2, h3, h4, h5, h6 {{ 
        color: var(--text-primary) !important; 
    }}

    .stCaption, [data-testid="stCaptionContainer"], small {{ 
        color: var(--text-secondary) !important; 
    }}
    
    /* الشريط الجانبي Sidebar */
    section[data-testid="stSidebar"] {{ 
        background-color: var(--bg-secondary) !important; 
        border-right: 1px solid var(--border); 
    }}
    section[data-testid="stSidebar"] * {{ 
        color: var(--text-primary) !important; 
    }}
    section[data-testid="stSidebar"] .stCaption {{ 
        color: var(--text-secondary) !important; 
    }}
    
    /* الأزرار General Buttons */
    div[data-testid="stButton"] button {{
        background-color: var(--button-bg) !important; 
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important; 
        border-radius: 10px !important;
        font-weight: 500 !important; 
        transition: background-color 0.1s ease, border-color 0.1s ease;
    }}
    div[data-testid="stButton"] button p {{ 
        color: var(--text-primary) !important; 
    }}
    div[data-testid="stButton"] button:hover {{ 
        background-color: var(--button-hover-bg) !important; 
        border-color: var(--accent) !important; 
    }}
    div[data-testid="stButton"] button:hover p {{ 
        color: var(--accent) !important; 
    }}
    
    /* أزرار القائمة الجانبية Navigation Links */
    div[data-testid="stSidebarNav"] li a,
    div[data-testid="stPageLink"] a {{
        background-color: var(--button-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stSidebarNav"] li a:hover,
    div[data-testid="stPageLink"] a:hover {{
        background-color: var(--button-hover-bg) !important;
        border-color: var(--accent) !important;
    }}
    div[data-testid="stSidebarNav"] li a span,
    div[data-testid="stPageLink"] p {{
        color: var(--text-primary) !important;
    }}

    /* فقاعات الـ Chat Messages */
    div[data-testid="stChatMessage"] {{
        max-width: 88%; 
        background-color: var(--assistant-bubble) !important;
        border: 1px solid var(--border); 
        border-radius: 14px;
    }}

    /* تلوين الحاوية السفلى بالكامل */
    footer, 
    [data-testid="stBottom"], 
    [data-testid="stBottomBlockContainer"],
    div[data-testid="stBottom"] > div {{
        background-color: var(--bg) !important;
        background: var(--bg) !important;
    }}

    /* إصلاح لون وشكل حقل الإدخال بالكامل */
    div[data-testid="stChatInput"] {{
        background-color: var(--input-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        max-width: 768px !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        font-size: 15px !important;
        color: var(--input-text) !important;
        background-color: transparent !important;
        -webkit-text-fill-color: var(--input-text) !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: var(--placeholder-text) !important;
        -webkit-text-fill-color: var(--placeholder-text) !important;
    }}
    div[data-testid="stChatInput"] button {{
        background-color: var(--accent) !important;
        border-radius: 50% !important;
    }}
    div[data-testid="stChatInput"] button svg {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }}

    /* Custom UI Components */
    .app-brand {{ display: flex; align-items: center; gap: 10px; padding: 4px 0 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 10px; }}
    .app-brand-text {{ display: flex; flex-direction: column; line-height: 1.25; }}
    .app-brand-title {{ font-weight: 650; font-size: 15.5px; color: var(--text-primary); }}
    .app-brand-subtitle {{ font-size: 12px; color: var(--text-secondary); }}
    .nav-section {{ margin-bottom: 14px; }}
    .kpi-card {{
        background: var(--card-bg); border: 1px solid var(--border); border-left: 3px solid var(--accent);
        border-radius: 10px; padding: 16px 18px; margin-bottom: 10px;
    }}
    .kpi-label {{ font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }}
    .kpi-value {{ font-size: 24px; font-weight: 650; color: var(--text-primary); }}
    .kpi-meta {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 4px; }}
    .company-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }}
    .company-badge {{ width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: white; }}
    .sidebar-footer {{ margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 12.5px; color: var(--text-secondary); text-align: center; }}
    .sidebar-footer a {{ color: var(--accent) !important; text-decoration: none; }}
    .answer-meta {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 8px; display: flex; align-items: center; gap: 6px; }}
    .chat-greeting {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }}
    .citation-card {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 12.5px; }}
    .citation-card .cc-top {{ display: flex; justify-content: space-between; align-items: center; color: var(--text-secondary); font-family: monospace; margin-bottom: 4px; }}
    .citation-card a {{ color: var(--accent) !important; text-decoration: none; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    @media (max-width: 640px) {{
        div[data-testid="stChatMessage"] {{ max-width: 96%; }}
        .kpi-value {{ font-size: 20px; }}
    }}
    </style>
    """)
