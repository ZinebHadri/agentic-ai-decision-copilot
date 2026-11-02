import os
from html import escape
from textwrap import dedent

import requests
import streamlit as st


API_URL = os.getenv(
    "COPILOT_API_URL",
    "http://127.0.0.1:8000",
)

st.set_page_config(
    page_title="Decision Copilot",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(content: str):
    st.html(
        dedent(content).strip()
    )


render_html(
    """
    <style>
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"] {
            background: #080b10 !important;
        }

        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        #MainMenu,
        footer {
            display: none !important;
            visibility: hidden !important;
        }

        .stApp {
            background:
                radial-gradient(
                    circle at 70% 0%,
                    rgba(110, 60, 220, 0.08),
                    transparent 28%
                ),
                #080b10;
            color: #f7f7fb;
        }

        .block-container {
            max-width: 1400px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        section[data-testid="stSidebar"] {
            background: #0a0d12 !important;
            border-right: 1px solid #1d2430 !important;
            width: 285px !important;
            min-width: 285px !important;
        }

        .brand {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 1.6rem;
        }

        .brand-logo {
            width: 48px;
            height: 48px;
            min-width: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 15px;
            background:
                linear-gradient(
                    135deg,
                    #6d3df5,
                    #a734ff
                );
            font-size: 1.35rem;
            box-shadow:
                0 0 25px rgba(130, 70, 255, 0.28);
        }

        .brand-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #f4f4f5;
        }

        .brand-sub {
            margin-top: 3px;
            font-size: 0.76rem;
            color: #a855f7;
            font-weight: 650;
        }

        .sidebar-label {
            color: #657084;
            text-transform: uppercase;
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            font-weight: 700;
            margin-top: 1.4rem;
            margin-bottom: 0.6rem;
        }

        .system-line {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            color: #a9b0bd;
            font-size: 0.76rem;
            margin-bottom: 0.7rem;
        }

        .system-good {
            color: #34d399;
            font-family: monospace;
            font-size: 0.7rem;
        }

        .dot {
            width: 8px;
            height: 8px;
            display: inline-block;
            border-radius: 50%;
            margin-right: 6px;
        }

        .dot.green {
            background: #22c55e;
            box-shadow:
                0 0 9px rgba(34, 197, 94, 0.7);
        }

        .dot.red {
            background: #ef4444;
        }

        div.stButton > button {
            width: 100%;
            border-radius: 11px !important;
            min-height: 44px !important;
            background: #121923 !important;
            color: #dce2eb !important;
            border: 1px solid #253044 !important;
            font-size: 0.82rem !important;
        }

        div.stButton > button:hover {
            border-color:
                rgba(168, 85, 247, 0.65) !important;
            background: #171d28 !important;
            color: white !important;
        }

        div.stButton > button[kind="primary"] {
            background:
                linear-gradient(
                    135deg,
                    #7040e8,
                    #9d2ff0
                ) !important;
            color: white !important;
            border: none !important;
            font-weight: 700 !important;
        }

        .home {
            padding-top: 3rem;
            max-width: 1050px;
            margin: 0 auto;
        }

        .eyebrow {
            display: inline-flex;
            padding: 0.4rem 0.7rem;
            border-radius: 999px;
            border:
                1px solid rgba(168, 85, 247, 0.3);
            background:
                rgba(126, 50, 190, 0.1);
            color: #c084fc;
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            font-weight: 700;
            text-transform: uppercase;
        }

        .home-title {
            max-width: 800px;
            font-size: 3.4rem;
            line-height: 1.03;
            font-weight: 820;
            letter-spacing: -0.05em;
            color: #f8fafc;
            margin-top: 1.2rem;
        }

        .home-text {
            max-width: 720px;
            margin-top: 1.1rem;
            font-size: 1.05rem;
            line-height: 1.65;
            color: #8b95a5;
        }

        .feature-grid {
            display: grid;
            grid-template-columns:
                repeat(4, 1fr);
            gap: 0.8rem;
            margin-top: 2.2rem;
        }

        .feature-card {
            border-radius: 15px;
            border: 1px solid #202938;
            background: #10151d;
            padding: 1rem;
        }

        .feature-icon {
            color: #a855f7;
            font-size: 1.15rem;
            margin-bottom: 0.6rem;
        }

        .feature-title {
            color: #f1f5f9;
            font-size: 0.86rem;
            font-weight: 720;
        }

        .feature-text {
            color: #7f8999;
            font-size: 0.75rem;
            line-height: 1.45;
            margin-top: 0.35rem;
        }

        .section-title {
            font-size: 1.5rem;
            font-weight: 780;
            color: #f4f4f5;
        }

        .section-sub {
            color: #7d8795;
            font-size: 0.84rem;
            margin-top: 0.3rem;
            max-width: 760px;
            line-height: 1.55;
        }

        .copilot-wrap {
            max-width: 1050px;
            margin: 0 auto;
            padding-top: 2rem;
        }

        .prompt-title {
            color: #8b95a5;
            font-size: 0.75rem;
            margin-top: 2rem;
            margin-bottom: 0.65rem;
        }

        div[data-testid="stTextInput"] input {
            min-height: 54px !important;
            background: #111821 !important;
            color: #f4f4f5 !important;
            border-radius: 13px !important;
            border: 1px solid #29354a !important;
            padding-left: 1rem !important;
        }

        .examples-label {
            margin-top: 1rem;
            color: #596477;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.66rem;
            font-weight: 700;
        }

        .examples {
            margin-top: 0.65rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .example-chip {
            padding: 0.48rem 0.7rem;
            border-radius: 10px;
            border: 1px solid #202938;
            background: #0f151d;
            color: #7e8999;
            font-size: 0.74rem;
            line-height: 1.35;
        }

        .clarification-card {
            margin-top: 1.8rem;
            border-radius: 16px;
            border:
                1px solid rgba(245, 158, 11, 0.30);
            background:
                rgba(120, 70, 12, 0.10);
            padding: 1.25rem;
        }

        .clarification-label {
            color: #fbbf24;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 750;
        }

        .clarification-message {
            color: #e5e7eb;
            margin-top: 0.65rem;
            line-height: 1.6;
            font-size: 0.9rem;
        }

        .required-list {
            margin-top: 0.8rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .required-item {
            padding: 0.35rem 0.55rem;
            border-radius: 8px;
            border:
                1px solid rgba(245, 158, 11, 0.22);
            color: #fbbf24;
            font-size: 0.72rem;
        }

        .clarification-example {
            margin-top: 0.85rem;
            padding: 0.65rem 0.75rem;
            background: #111821;
            border: 1px solid #29354a;
            border-radius: 9px;
            color: #cbd5e1;
            font-size: 0.77rem;
        }

        .analysis-divider {
            height: 1px;
            width: 100%;
            background: #1b2330;
            margin-top: 2rem;
            margin-bottom: 1.8rem;
        }

        .pipeline {
            display: grid;
            grid-template-columns:
                1fr 28px
                1fr 28px
                1fr 28px
                1fr 28px
                1fr;
            gap: 0.4rem;
            align-items: center;
            margin-top: 1rem;
        }

        .pipeline-card {
            min-height: 112px;
            background: #121923;
            border: 1px solid #263044;
            border-radius: 13px;
            padding: 0.85rem;
            position: relative;
        }

        .pipeline-title {
            font-size: 0.84rem;
            font-weight: 720;
            color: #f0f2f5;
        }

        .pipeline-desc {
            font-size: 0.7rem;
            color: #8390a2;
            margin-top: 0.3rem;
            line-height: 1.35;
        }

        .pipeline-number {
            color: #a855f7;
            font-size: 0.7rem;
            margin-bottom: 0.5rem;
        }

        .pipeline-check {
            position: absolute;
            right: 10px;
            top: 8px;
            color: #34d399;
        }

        .pipeline-arrow {
            text-align: center;
            color: #755cff;
            font-size: 1.2rem;
        }

        .result-grid {
            display: grid;
            grid-template-columns:
                1fr 1fr;
            gap: 1rem;
            margin-top: 1.2rem;
        }

        .result-card {
            border-radius: 16px;
            border: 1px solid #202938;
            background: #10151d;
            padding: 1.1rem;
        }

        .result-card.answer {
            border-color:
                rgba(168, 85, 247, 0.35);
        }

        .result-label {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #728096;
            font-size: 0.67rem;
            margin-bottom: 0.5rem;
        }

        .result-value {
            color: #f3f4f6;
            font-size: 0.88rem;
            line-height: 1.65;
        }

        .intent {
            color: #d580ff;
            font-weight: 800;
            font-family: monospace;
        }

        .tool {
            margin-top: 0.45rem;
            padding: 0.5rem 0.65rem;
            border-radius: 8px;
            border:
                1px solid rgba(52, 211, 153, 0.2);
            background:
                rgba(16, 185, 129, 0.07);
            color: #34d399;
            font-family: monospace;
            font-size: 0.75rem;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.8rem;
        }

        .chip {
            padding: 0.35rem 0.55rem;
            border-radius: 8px;
            border: 1px solid #263044;
            background: #151c27;
            color: #adb7c5;
            font-size: 0.68rem;
        }

        .chip.green {
            color: #34d399;
        }

        .architecture-grid {
            display: grid;
            grid-template-columns:
                repeat(3, 1fr);
            gap: 1rem;
            margin-top: 1.5rem;
        }

        .architecture-card {
            border-radius: 15px;
            border: 1px solid #202938;
            background: #10151d;
            padding: 1rem;
        }

        .architecture-title {
            font-size: 0.9rem;
            font-weight: 720;
            color: #f1f5f9;
        }

        .architecture-text {
            color: #7e8999;
            font-size: 0.76rem;
            line-height: 1.5;
            margin-top: 0.4rem;
        }

        .footer {
            margin-top: 2rem;
            text-align: center;
            color: #485260;
            font-size: 0.68rem;
        }
    </style>
    """
)


if "page" not in st.session_state:
    st.session_state.page = "Home"

if "question" not in st.session_state:
    st.session_state.question = ""

if "response_data" not in st.session_state:
    st.session_state.response_data = None

if "error_message" not in st.session_state:
    st.session_state.error_message = None


def check_api_health():
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=5,
        )

        if response.status_code == 200:
            return True, response.json()

        return False, None

    except requests.RequestException:
        return False, None


def ask_copilot(question):
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={
                "question": question
            },
            timeout=300,
        )

        if response.status_code == 200:
            return response.json(), None

        try:
            detail = (
                response.json()
                .get(
                    "detail",
                    "Unknown API error",
                )
            )
        except Exception:
            detail = response.text

        return (
            None,
            f"API error {response.status_code}: {detail}",
        )

    except requests.Timeout:
        return (
            None,
            "The local model is taking longer than expected.",
        )

    except requests.RequestException:
        return (
            None,
            "Could not connect to the backend.",
        )


api_ok, health_data = check_api_health()

sales_rows_text = ""

if health_data:
    sales_rows_text = (
        f"{health_data['sales_rows']:,}"
    )


with st.sidebar:
    render_html(
        """
        <div class="brand">
            <div class="brand-logo">
                ✦
            </div>

            <div>
                <div class="brand-title">
                    Decision Copilot
                </div>

                <div class="brand-sub">
                    Agentic Analytics
                </div>
            </div>
        </div>
        """
    )

    render_html(
        """
        <div class="sidebar-label">
            Navigation
        </div>
        """
    )

    if st.button(
        "⌂ Home",
        use_container_width=True,
    ):
        st.session_state.page = "Home"
        st.rerun()

    if st.button(
        "✦ Ask Copilot",
        use_container_width=True,
    ):
        st.session_state.page = "Copilot"
        st.rerun()

    if st.button(
        "⌁ Architecture",
        use_container_width=True,
    ):
        st.session_state.page = "Architecture"
        st.rerun()

    render_html(
        """
        <div class="sidebar-label">
            System
        </div>
        """
    )

    if api_ok:
        render_html(
            """
            <div class="system-line">
                <span>
                    <span class="dot green"></span>
                    FastAPI
                </span>

                <span class="system-good">
                    online
                </span>
            </div>
            """
        )

    else:
        render_html(
            """
            <div class="system-line">
                <span>
                    <span class="dot red"></span>
                    FastAPI
                </span>

                <span style="color:#ef4444;">
                    offline
                </span>
            </div>
            """
        )

    render_html(
        """
        <div class="system-line">
            <span>
                Qwen 2.5
            </span>

            <span class="system-good">
                local
            </span>
        </div>

        <div class="system-line">
            <span>
                LangGraph
            </span>

            <span class="system-good">
                active
            </span>
        </div>
        """
    )

    if health_data:
        render_html(
            f"""
            <div class="system-line">
                <span>
                    Validated rows
                </span>

                <span>
                    {sales_rows_text}
                </span>
            </div>
            """
        )


if st.session_state.page == "Home":
    render_html(
        """
        <div class="home">

            <div class="eyebrow">
                Agentic AI · Analytics
            </div>

            <div class="home-title">
                Ask.
                Analyze.
                Verify.
            </div>

            <div class="home-text">
                Decision Copilot understands
                natural-language questions,
                plans the required analysis,
                executes deterministic Python
                tools and verifies every answer
                before returning it.
            </div>

            <div class="feature-grid">

                <div class="feature-card">
                    <div class="feature-icon">
                        ◈
                    </div>

                    <div class="feature-title">
                        Hybrid routing
                    </div>

                    <div class="feature-text">
                        Local LLM combined with
                        deterministic routing.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        ⌁
                    </div>

                    <div class="feature-title">
                        Agentic planning
                    </div>

                    <div class="feature-text">
                        LangGraph coordinates
                        multi-step analyses.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        &lt;/&gt;
                    </div>

                    <div class="feature-title">
                        Analytics tools
                    </div>

                    <div class="feature-text">
                        Performance, revenue,
                        customers, returns
                        and anomalies.
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">
                        ✓
                    </div>

                    <div class="feature-title">
                        Verification
                    </div>

                    <div class="feature-text">
                        Numeric checks,
                        quality validation
                        and safe fallback.
                    </div>
                </div>

            </div>

        </div>
        """
    )

    st.write("")

    _, center, _ = st.columns(
        [1, 1.1, 1]
    )

    with center:
        if st.button(
            "Open Decision Copilot →",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.page = "Copilot"
            st.rerun()


elif st.session_state.page == "Copilot":
    render_html(
        """
        <div class="copilot-wrap">

            <div class="section-title">
                Ask Decision Copilot
            </div>

            <div class="section-sub">
                Ask about performance,
                revenue changes, customers,
                returns or unusual activity.
            </div>

            <div class="prompt-title">
                Ask your question
            </div>

        </div>
        """
    )

    question_col, button_col = st.columns(
        [6, 1.2]
    )

    with question_col:
        question = st.text_input(
            "Question",
            value=st.session_state.question,
            placeholder=(
                "Ask your question..."
            ),
            label_visibility="collapsed",
        )

    with button_col:
        analyze = st.button(
            "Analyze →",
            type="primary",
            use_container_width=True,
        )

    render_html(
        """
        <div class="examples-label">
            Try asking
        </div>

        <div class="examples">

            <div class="example-chip">
                “How did September 2011 perform?”
            </div>

            <div class="example-chip">
                “Why did revenue fall from March 2011
                to April 2011?”
            </div>

            <div class="example-chip">
                “Which customers contributed most
                to the decline from March 2011
                to April 2011?”
            </div>

            <div class="example-chip">
                “Was April 2011 unusually weak?”
            </div>

            <div class="example-chip">
                “What were the returns
                in April 2011?”
            </div>

        </div>
        """
    )

    if analyze:
        clean_question = question.strip()

        st.session_state.error_message = None

        if not clean_question:
            st.warning(
                "Enter a question first."
            )

        elif not api_ok:
            st.error(
                "FastAPI backend is offline."
            )

        else:
            with st.spinner(
                "Routing · planning · executing · verifying..."
            ):
                (
                    response_data,
                    error,
                ) = ask_copilot(
                    clean_question
                )

            if error:
                st.session_state.error_message = error

            else:
                st.session_state.response_data = response_data
                st.session_state.question = ""
                st.rerun()

    if st.session_state.error_message:
        st.error(
            st.session_state.error_message
        )

    data = st.session_state.response_data

    if data:
        needs_clarification = (
            data.get(
                "needs_clarification",
                False,
            )
        )

        if needs_clarification:
            clarification = data.get(
                "clarification",
                {},
            )

            title = escape(
                str(
                    clarification.get(
                        "title",
                        "More context needed",
                    )
                )
            )

            message = escape(
                str(
                    clarification.get(
                        "message",
                        "",
                    )
                )
            )

            required_fields = (
                clarification.get(
                    "required_fields",
                    [],
                )
            )

            examples = clarification.get(
                "examples",
                [],
            )

            required_html = "".join(
                (
                    '<div class="required-item">'
                    f'{escape(str(field))}'
                    '</div>'
                )
                for field in required_fields
            )

            examples_html = "".join(
                (
                    '<div class="clarification-example">'
                    f'{escape(str(example))}'
                    '</div>'
                )
                for example in examples
            )

            render_html(
                f"""
                <div class="clarification-card">

                    <div class="clarification-label">
                        {title}
                    </div>

                    <div class="clarification-message">
                        {message}
                    </div>

                    <div class="required-list">
                        {required_html}
                    </div>

                    {examples_html}

                </div>
                """
            )

        else:
            render_html(
                """
                <div class="analysis-divider"></div>
                """
            )

            completed_tools = data.get(
                "completed_tools",
                [],
            )

            verification = data.get(
                "verification",
                {},
            )

            verification_passed = (
                verification.get(
                    "passed",
                    False,
                )
            )

            render_html(
                f"""
                <div class="pipeline">

                    <div class="pipeline-card">
                        <div class="pipeline-check">
                            ✓
                        </div>

                        <div class="pipeline-number">
                            01
                        </div>

                        <div class="pipeline-title">
                            Router
                        </div>

                        <div class="pipeline-desc">
                            Intent and period detection
                        </div>
                    </div>

                    <div class="pipeline-arrow">
                        →
                    </div>

                    <div class="pipeline-card">
                        <div class="pipeline-check">
                            ✓
                        </div>

                        <div class="pipeline-number">
                            02
                        </div>

                        <div class="pipeline-title">
                            Planner
                        </div>

                        <div class="pipeline-desc">
                            Hybrid analysis planning
                        </div>
                    </div>

                    <div class="pipeline-arrow">
                        →
                    </div>

                    <div class="pipeline-card">
                        <div class="pipeline-check">
                            {
                                "✓"
                                if completed_tools
                                else ""
                            }
                        </div>

                        <div class="pipeline-number">
                            03
                        </div>

                        <div class="pipeline-title">
                            Tools
                        </div>

                        <div class="pipeline-desc">
                            Deterministic Python analytics
                        </div>
                    </div>

                    <div class="pipeline-arrow">
                        →
                    </div>

                    <div class="pipeline-card">
                        <div class="pipeline-check">
                            {
                                "✓"
                                if verification_passed
                                else ""
                            }
                        </div>

                        <div class="pipeline-number">
                            04
                        </div>

                        <div class="pipeline-title">
                            Verifier
                        </div>

                        <div class="pipeline-desc">
                            Numeric + quality checks
                        </div>
                    </div>

                    <div class="pipeline-arrow">
                        →
                    </div>

                    <div class="pipeline-card">
                        <div class="pipeline-check">
                            ✓
                        </div>

                        <div class="pipeline-number">
                            05
                        </div>

                        <div class="pipeline-title">
                            Final answer
                        </div>

                        <div class="pipeline-desc">
                            Grounded response
                        </div>
                    </div>

                </div>
                """
            )

            plan = data.get(
                "plan",
                [],
            )

            plan_text = (
                " → ".join(plan)
                if plan
                else "No plan"
            )

            intent = (
                plan[0].upper()
                if plan
                else "UNKNOWN"
            )

            tools_html = "".join(
                (
                    '<div class="tool">'
                    f'&gt; {escape(tool)}()'
                    '</div>'
                )
                for tool in completed_tools
            )

            answer = escape(
                str(
                    data.get(
                        "final_answer",
                        "",
                    )
                )
            )

            source = escape(
                str(
                    verification.get(
                        "source",
                        "llm",
                    )
                )
            )

            fallback = (
                "Yes"
                if data.get(
                    "used_fallback",
                    False,
                )
                else "No"
            )

            attempts = data.get(
                "generation_attempts",
                0,
            )

            verified_text = (
                "✓ Verified"
                if verification_passed
                else "Verification pending"
            )

            render_html(
                f"""
                <div class="result-grid">

                    <div class="result-card">

                        <div class="result-label">
                            Agent Inspector
                        </div>

                        <div class="result-value">

                            <div class="intent">
                                {escape(intent)}
                            </div>

                            <br>

                            Plan:
                            {escape(plan_text)}

                            <br><br>

                            {tools_html}

                        </div>

                    </div>

                    <div class="result-card answer">

                        <div class="result-label">
                            Verified Answer
                        </div>

                        <div class="result-value">
                            {answer}
                        </div>

                        <div class="chip-row">

                            <div class="chip green">
                                {verified_text}
                            </div>

                            <div class="chip">
                                Source: {source}
                            </div>

                            <div class="chip">
                                Fallback: {fallback}
                            </div>

                            <div class="chip">
                                Attempts: {attempts}
                            </div>

                        </div>

                    </div>

                </div>
                """
            )

            evidence_col, verification_col = (
                st.columns(2)
            )

            with evidence_col:
                with st.expander(
                    "Analytics evidence"
                ):
                    st.json(
                        data.get(
                            "tool_results",
                            {},
                        )
                    )

            with verification_col:
                with st.expander(
                    "Verification report"
                ):
                    st.json(
                        verification
                    )


elif st.session_state.page == "Architecture":
    render_html(
        """
        <div class="section-title">
            System Architecture
        </div>

        <div class="section-sub">
            Local LLM reasoning,
            deterministic analytics
            and strict answer verification.
        </div>

        <div class="architecture-grid">

            <div class="architecture-card">
                <div class="architecture-title">
                    1. LLM Router
                </div>

                <div class="architecture-text">
                    Qwen classifies intent
                    and extracts periods.
                </div>
            </div>

            <div class="architecture-card">
                <div class="architecture-title">
                    2. Hybrid Planner
                </div>

                <div class="architecture-text">
                    LLM planning with
                    deterministic guardrails.
                </div>
            </div>

            <div class="architecture-card">
                <div class="architecture-title">
                    3. LangGraph
                </div>

                <div class="architecture-text">
                    Orchestrates single-step
                    and multi-step workflows.
                </div>
            </div>

            <div class="architecture-card">
                <div class="architecture-title">
                    4. Analytics Tools
                </div>

                <div class="architecture-text">
                    Performance, revenue,
                    customers, returns and anomalies.
                </div>
            </div>

            <div class="architecture-card">
                <div class="architecture-title">
                    5. Verification
                </div>

                <div class="architecture-text">
                    Numeric grounding
                    and quality validation.
                </div>
            </div>

            <div class="architecture-card">
                <div class="architecture-title">
                    6. Safe Fallback
                </div>

                <div class="architecture-text">
                    Failed LLM answers become
                    deterministic grounded answers.
                </div>
            </div>

        </div>
        """
    )


if health_data:
    render_html(
        f"""
        <div class="footer">
            Decision Copilot ·
            Qwen 2.5 0.5B ·
            LangGraph ·
            FastAPI ·
            {sales_rows_text}
            validated sales rows
        </div>
        """
    )