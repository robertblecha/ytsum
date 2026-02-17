import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import anthropic
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Summarizer",
    page_icon="▶",
    layout="wide",
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #0a0a0a;
    color: #f0f0f0;
}

h1, h2, h3 {
    font-family: 'Space Mono', monospace !important;
}

.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #f0f0f0;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-family: 'DM Sans', sans-serif;
    color: #666;
    font-size: 1rem;
    margin-bottom: 2rem;
}

.accent { color: #ff4d4d; }

.card {
    background: #141414;
    border: 1px solid #222;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
}

.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #ff4d4d;
    margin-bottom: 0.8rem;
}

.summary-text {
    font-size: 1.05rem;
    line-height: 1.75;
    color: #d0d0d0;
}

.bullet-item {
    display: flex;
    gap: 0.8rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1e1e1e;
    font-size: 0.95rem;
    color: #c0c0c0;
    line-height: 1.5;
}

.bullet-dot {
    color: #ff4d4d;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 2px;
}

.transcript-box {
    max-height: 350px;
    overflow-y: auto;
    font-size: 0.88rem;
    color: #888;
    line-height: 1.7;
    font-family: 'DM Sans', sans-serif;
    padding-right: 0.5rem;
}

.transcript-box::-webkit-scrollbar { width: 4px; }
.transcript-box::-webkit-scrollbar-track { background: #0a0a0a; }
.transcript-box::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }

.answer-box {
    background: #0f0f0f;
    border-left: 3px solid #ff4d4d;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.98rem;
    color: #d0d0d0;
    line-height: 1.7;
}

.stTextInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #f0f0f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput > div > div > input:focus {
    border-color: #ff4d4d !important;
    box-shadow: 0 0 0 2px rgba(255,77,77,0.15) !important;
}

.stButton > button {
    background: #ff4d4d !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}

.stButton > button:hover {
    opacity: 0.85 !important;
}

.stExpander {
    border: 1px solid #222 !important;
    border-radius: 10px !important;
    background: #141414 !important;
}

div[data-testid="stHorizontalBlock"] { gap: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_transcript(video_id: str) -> tuple[str, str]:
    """Returns (transcript_text, language_used)"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        all_transcripts = list(transcript_list)

        if not all_transcripts:
            raise RuntimeError("Pro toto video nebyly nalezeny žádné titulky.")

        def preference(t):
            if t.language_code == "cs" and not t.is_generated:
                return 0
            if t.language_code == "en" and not t.is_generated:
                return 1
            if t.language_code == "cs":
                return 2
            if t.language_code == "en":
                return 3
            if not t.is_generated:
                return 4
            return 5

        all_transcripts.sort(key=preference)
        chosen = all_transcripts[0]
        segments = chosen.fetch()
        text = " ".join(s["text"] for s in segments)
        return text, f"{chosen.language_code} ('auto' if chosen.is_generated else 'manual')"

    except TranscriptsDisabled:
        raise RuntimeError("Titulky jsou pro toto video zakázány.")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Chyba: {type(e).__name__}: {e}")


def get_claude_client() -> anthropic.Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("Chybí ANTHROPIC_API_KEY v Streamlit secrets.")
    return anthropic.Anthropic(api_key=api_key)


def claude_analyze(transcript: str, video_url: str) -> dict:
    client = get_claude_client()
    prompt = f"""Analyzuj následující transkript YouTube videa a vrať odpověď ve formátu níže.
URL videa: {video_url}

TRANSKRIPT:
{transcript[:12000]}

Odpověz POUZE v tomto formátu (nic jiného nepřidávej):

SUMMARY:
[2–4 věty shrnující celé video]

BULLETS:
- [klíčový bod 1]
- [klíčový bod 2]
- [klíčový bod 3]
- [klíčový bod 4]
- [klíčový bod 5]
(přidej více bodů pokud je obsah bohatý, max 10)

Odpovídej ve stejném jazyce, v jakém je transkript. Pokud je smíšený, preferuj češtinu."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text

    summary, bullets = "", []
    if "SUMMARY:" in raw and "BULLETS:" in raw:
        summary_part = raw.split("BULLETS:")[0].replace("SUMMARY:", "").strip()
        bullets_part = raw.split("BULLETS:")[1].strip()
        summary = summary_part
        bullets = [
            line.lstrip("- •").strip()
            for line in bullets_part.splitlines()
            if line.strip().startswith("-") or line.strip().startswith("•")
        ]
    else:
        summary = raw

    return {"summary": summary, "bullets": bullets}


def claude_answer(transcript: str, question: str) -> str:
    client = get_claude_client()
    prompt = f"""Na základě tohoto transkriptu YouTube videa odpověz na otázku uživatele.

TRANSKRIPT:
{transcript[:12000]}

OTÁZKA: {question}

Odpověz stručně a přesně. Pokud odpověď není v transkriptu, řekni to."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">YT <span class="accent">//</span> Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Transkript · Shrnutí · Q&A — pro jakékoliv YouTube video</div>', unsafe_allow_html=True)

url_input = st.text_input(
    label="YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

col_btn, col_space = st.columns([1, 5])
with col_btn:
    analyze_btn = st.button("▶  ANALYZOVAT")

st.markdown("---")

if analyze_btn and url_input:
    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("Nepodařilo se rozpoznat YouTube URL. Zkus jiný formát.")
    else:
        with st.spinner("Stahuji transkript..."):
            try:
                transcript_text, lang = get_transcript(video_id)
                st.session_state["transcript"] = transcript_text
                st.session_state["video_url"] = url_input
                st.session_state["video_id"] = video_id
                st.session_state["lang"] = lang
                st.session_state["analysis"] = None
            except RuntimeError as e:
                st.error(str(e))
                st.stop()

        with st.spinner("Claude analyzuje video..."):
            try:
                analysis = claude_analyze(transcript_text, url_input)
                st.session_state["analysis"] = analysis
            except RuntimeError as e:
                st.error(str(e))
                st.stop()

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.get("analysis"):
    analysis = st.session_state["analysis"]
    transcript_text = st.session_state["transcript"]
    video_id = st.session_state["video_id"]

    # Video embed
    st.markdown(f"""
    <div class="card" style="padding:0; overflow:hidden; border-radius:12px;">
        <iframe width="100%" height="340" src="https://www.youtube.com/embed/{video_id}"
        frameborder="0" allowfullscreen style="display:block;"></iframe>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Summary
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Summary</div>
            <div class="summary-text">{analysis["summary"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Bullets
        bullets_html = "".join(
            f'<div class="bullet-item"><span class="bullet-dot">→</span><span>{b}</span></div>'
            for b in analysis["bullets"]
        )
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Klíčové body</div>
            {bullets_html}
        </div>
        """, unsafe_allow_html=True)

    # Transcript
    with st.expander("📄  Zobrazit plný transkript"):
        st.markdown(f'<div class="transcript-box">{transcript_text}</div>', unsafe_allow_html=True)

    # Q&A
    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Zeptej se na video</div>', unsafe_allow_html=True)
    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "Otázka",
            placeholder="Co říká o...? Kdy se zmínil o...?",
            label_visibility="collapsed",
            key="question_input"
        )
    with btn_col:
        ask_btn = st.button("ZEPTAT SE")

    if ask_btn and question:
        with st.spinner("Hledám odpověď..."):
            answer = claude_answer(transcript_text, question)
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

elif not url_input:
    st.markdown("""
    <div style="text-align:center; color:#333; padding: 3rem 0; font-family: 'Space Mono', monospace; font-size:0.85rem; letter-spacing:2px;">
        VLOŽ YOUTUBE URL A STISKNI ANALYZOVAT
    </div>
    """, unsafe_allow_html=True)
