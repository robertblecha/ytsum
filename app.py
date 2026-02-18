import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import anthropic
import re
import json
import time
import urllib.request
from datetime import datetime, timezone

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Summarizer",
    page_icon="▶",
    layout="wide",
)

# ── Buy Me a Coffee URL — change this to your own ─────────────────────────────
BMAC_URL = "https://buymeacoffee.com/robertiscreating"

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp { background: #0a0a0a; color: #f0f0f0; }

h1, h2, h3 { font-family: 'Space Mono', monospace !important; }

.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #f0f0f0;
    letter-spacing: -1px;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}

.subtitle { font-family: 'DM Sans', sans-serif; color: #666; font-size: 1rem; margin-bottom: 2rem; }
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

.summary-text { font-size: 1.05rem; line-height: 1.75; color: #d0d0d0; }

.bullet-item {
    display: flex;
    gap: 0.8rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid #1e1e1e;
    font-size: 0.95rem;
    color: #c0c0c0;
    line-height: 1.5;
}

.bullet-dot { color: #ff4d4d; font-weight: 700; flex-shrink: 0; margin-top: 2px; }

.transcript-box {
    max-height: 350px;
    overflow-y: auto;
    font-size: 0.88rem;
    color: #888;
    line-height: 1.7;
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

/* Recent videos feed */
.feed-card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 0.75rem;
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
}
.feed-card:hover { border-color: #333; }
.feed-thumb {
    width: 80px;
    height: 45px;
    object-fit: cover;
    border-radius: 6px;
    flex-shrink: 0;
    background: #1a1a1a;
}
.feed-title {
    font-size: 0.82rem;
    color: #ccc;
    line-height: 1.4;
    margin-bottom: 0.3rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.feed-meta {
    font-size: 0.72rem;
    color: #555;
    font-family: 'Space Mono', monospace;
}

/* Progress steps */
.progress-step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0;
    font-size: 0.9rem;
    color: #888;
    border-bottom: 1px solid #1a1a1a;
}
.progress-step.done { color: #4caf50; }
.progress-step.active { color: #ff4d4d; }
.step-icon { font-size: 1rem; width: 1.4rem; text-align: center; }

/* Input & buttons */
.stTextInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #f0f0f0 !important;
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
.stButton > button:hover { opacity: 0.85 !important; }

.stExpander { border: 1px solid #222 !important; border-radius: 10px !important; background: #141414 !important; }

/* Footer */
.footer {
    margin-top: 4rem;
    padding: 2rem 0 1rem 0;
    border-top: 1px solid #1a1a1a;
    text-align: center;
}
.bmac-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #FFDD00;
    color: #000 !important;
    text-decoration: none !important;
    padding: 0.6rem 1.4rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: opacity 0.2s;
}
.bmac-btn:hover { opacity: 0.85; }
.footer-note { color: #444; font-size: 0.78rem; margin-top: 0.8rem; font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    for p in [r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})"]:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_video_title(video_id: str) -> str:
    """Fetch video title from YouTube oEmbed API (no key needed)"""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("title", "Unknown title")
    except Exception:
        return "Unknown title"


def get_user_location() -> dict:
    """Get approximate location from IP geolocation"""
    try:
        with urllib.request.urlopen("https://ipapi.co/json/", timeout=5) as r:
            data = json.loads(r.read())
            country = data.get("country_name", "Unknown")
            city = data.get("city", "Unknown")
            country_code = data.get("country_code", "").lower()
            flag = "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper()) if country_code else "🌍"
            return {"country": country, "city": city, "flag": flag}
    except Exception:
        return {"country": "Unknown", "city": "Unknown", "flag": "🌍"}


def time_ago(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        diff = datetime.now(timezone.utc) - dt
        s = int(diff.total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            return f"{s // 60}m ago"
        if s < 86400:
            return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return ""


def get_transcript(video_id: str) -> tuple[str, str]:
    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
        all_transcripts = list(transcript_list)

        if not all_transcripts:
            raise RuntimeError("No subtitles found for this video.")

        def preference(t):
            if t.language_code == "cs" and not t.is_generated: return 0
            if t.language_code == "en" and not t.is_generated: return 1
            if t.language_code == "cs": return 2
            if t.language_code == "en": return 3
            if not t.is_generated: return 4
            return 5

        all_transcripts.sort(key=preference)
        chosen = all_transcripts[0]
        fetched = ytt.fetch(video_id, languages=[chosen.language_code])
        text = " ".join(s.text for s in fetched)
        lang_type = "auto" if chosen.is_generated else "manual"
        return text, f"{chosen.language_code} ({lang_type})"

    except TranscriptsDisabled:
        raise RuntimeError("Subtitles are disabled for this video.")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error: {type(e).__name__}: {e}")


def get_claude_client() -> anthropic.Anthropic:
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY in Streamlit secrets.")
    return anthropic.Anthropic(api_key=api_key)


def claude_analyze(transcript: str, video_url: str) -> dict:
    client = get_claude_client()
    prompt = f"""Analyze the following YouTube video transcript and respond ONLY in the format below.
Video URL: {video_url}

TRANSCRIPT:
{transcript[:12000]}

Respond ONLY in this exact format (nothing else):

SUMMARY:
[2-4 sentences summarizing the entire video]

BULLETS:
- [key point 1]
- [key point 2]
- [key point 3]
- [key point 4]
- [key point 5]
(add more bullets if content is rich, max 10)

Respond in the same language as the transcript. If mixed, prefer English."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text

    summary, bullets = "", []
    if "SUMMARY:" in raw and "BULLETS:" in raw:
        summary = raw.split("BULLETS:")[0].replace("SUMMARY:", "").strip()
        bullets_part = raw.split("BULLETS:")[1].strip()
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
    prompt = f"""Based on this YouTube video transcript, answer the user's question.

TRANSCRIPT:
{transcript[:12000]}

QUESTION: {question}

Answer concisely and accurately. If the answer is not in the transcript, say so."""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# ── Persistent storage helpers ─────────────────────────────────────────────────

async def load_recent_videos():
    try:
        result = await st.context.storage.get("recent_videos", True)
        if result:
            return json.loads(result["value"])
    except Exception:
        pass
    return []


async def save_recent_videos(videos: list):
    try:
        await st.context.storage.set("recent_videos", json.dumps(videos), True)
    except Exception:
        pass


def load_recent_videos_sync() -> list:
    """Load from session state cache (populated on startup)"""
    return st.session_state.get("_recent_videos_cache", [])


def add_to_recent(video_id: str, title: str, location: dict):
    """Add video to recent list stored in session state"""
    videos = load_recent_videos_sync()
    # Remove duplicate if exists
    videos = [v for v in videos if v.get("video_id") != video_id]
    entry = {
        "video_id": video_id,
        "title": title,
        "thumb": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "flag": location["flag"],
        "city": location["city"],
        "country": location["country"],
    }
    videos.insert(0, entry)
    videos = videos[:20]  # Keep last 20
    st.session_state["_recent_videos_cache"] = videos
    # Also persist to Streamlit storage if available
    try:
        import asyncio
        # Store in session for persistence across reloads via query params workaround
        st.session_state["_recent_videos_json"] = json.dumps(videos)
    except Exception:
        pass


# ── Initialize session state ──────────────────────────────────────────────────

if "_recent_videos_cache" not in st.session_state:
    # Try to load from a shared source — use a simple file-based approach via secrets or default empty
    st.session_state["_recent_videos_cache"] = []

# Use Streamlit's built-in storage API for shared state across users
@st.cache_resource
def get_shared_store():
    """In-memory shared store that persists for the lifetime of the server process"""
    return {"recent_videos": []}

shared = get_shared_store()


def add_to_shared_recent(video_id: str, title: str, location: dict):
    entry = {
        "video_id": video_id,
        "title": title,
        "thumb": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "flag": location["flag"],
        "city": location["city"],
        "country": location["country"],
    }
    videos = shared["recent_videos"]
    videos = [v for v in videos if v.get("video_id") != video_id]
    videos.insert(0, entry)
    shared["recent_videos"] = videos[:20]


def get_shared_recent() -> list:
    return shared.get("recent_videos", [])


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">YT <span class="accent">//</span> Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Transcript · Summary · Q&A — for any YouTube video</div>', unsafe_allow_html=True)

url_input = st.text_input(
    label="YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    label_visibility="collapsed",
)

col_btn, col_space = st.columns([1, 5])
with col_btn:
    analyze_btn = st.button("▶  ANALYZE")

# ── Progress + Analysis ───────────────────────────────────────────────────────

if analyze_btn and url_input:
    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("Couldn't recognize YouTube URL. Try a different format.")
    else:
        st.markdown("---")
        progress_placeholder = st.empty()

        def render_progress(steps):
            icons = {"done": "✅", "active": "⏳", "pending": "○"}
            colors = {"done": "#4caf50", "active": "#ff4d4d", "pending": "#444"}
            html = '<div class="card" style="padding:1rem 1.5rem;">'
            html += '<div class="section-label">Processing</div>'
            for label, state in steps:
                icon = icons[state]
                color = colors[state]
                html += f'<div class="progress-step {state}"><span class="step-icon">{icon}</span><span style="color:{color}">{label}</span></div>'
            html += '</div>'
            progress_placeholder.markdown(html, unsafe_allow_html=True)

        # Step 1: Fetch transcript
        render_progress([
            ("Fetching transcript from YouTube...", "active"),
            ("Analyzing with Claude AI...", "pending"),
            ("Getting your location...", "pending"),
        ])

        try:
            transcript_text, lang = get_transcript(video_id)
            st.session_state["transcript"] = transcript_text
            st.session_state["video_url"] = url_input
            st.session_state["video_id"] = video_id
            st.session_state["lang"] = lang
            st.session_state["analysis"] = None
        except RuntimeError as e:
            progress_placeholder.empty()
            st.error(str(e))
            st.stop()

        # Step 2: Claude analysis
        render_progress([
            ("Fetching transcript from YouTube...", "done"),
            ("Analyzing with Claude AI...", "active"),
            ("Getting your location...", "pending"),
        ])

        try:
            analysis = claude_analyze(transcript_text, url_input)
            st.session_state["analysis"] = analysis
        except RuntimeError as e:
            progress_placeholder.empty()
            st.error(str(e))
            st.stop()

        # Step 3: Location + title
        render_progress([
            ("Fetching transcript from YouTube...", "done"),
            ("Analyzing with Claude AI...", "done"),
            ("Getting your location...", "active"),
        ])

        location = get_user_location()
        title = get_video_title(video_id)
        add_to_shared_recent(video_id, title, location)

        render_progress([
            ("Fetching transcript from YouTube...", "done"),
            ("Analyzing with Claude AI...", "done"),
            ("Getting your location...", "done"),
        ])

        time.sleep(0.5)
        progress_placeholder.empty()

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.get("analysis"):
    st.markdown("---")
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
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Summary</div>
            <div class="summary-text">{analysis["summary"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        bullets_html = "".join(
            f'<div class="bullet-item"><span class="bullet-dot">→</span><span>{b}</span></div>'
            for b in analysis["bullets"]
        )
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Key Points</div>
            {bullets_html}
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📄  Show full transcript"):
        st.markdown(f'<div class="transcript-box">{transcript_text}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Ask a question about this video</div>', unsafe_allow_html=True)
    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "Question",
            placeholder="What does it say about...? When did they mention...?",
            label_visibility="collapsed",
            key="question_input"
        )
    with btn_col:
        ask_btn = st.button("ASK")

    if ask_btn and question:
        with st.spinner("Finding the answer..."):
            answer = claude_answer(transcript_text, question)
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

# ── Recent videos feed ────────────────────────────────────────────────────────

st.markdown("---")
recent = get_shared_recent()

if recent:
    st.markdown('<div class="section-label">Recently summarized by others</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, v in enumerate(recent[:10]):
        with cols[i % 2]:
            ago = time_ago(v.get("timestamp", ""))
            geo = f"{v.get('flag','')} {v.get('city','')}, {v.get('country','')}"
            st.markdown(f"""
            <div class="feed-card">
                <img class="feed-thumb" src="{v['thumb']}" onerror="this.style.display='none'"/>
                <div>
                    <div class="feed-title">{v['title']}</div>
                    <div class="feed-meta">{ago} &nbsp;·&nbsp; {geo}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center; color:#2a2a2a; padding: 1.5rem 0; font-family: 'Space Mono', monospace; font-size:0.78rem; letter-spacing:2px;">
        NO VIDEOS SUMMARIZED YET — BE THE FIRST
    </div>
    """, unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────

if not st.session_state.get("analysis") and not analyze_btn:
    st.markdown("""
    <div style="text-align:center; color:#2a2a2a; padding: 2rem 0; font-family: 'Space Mono', monospace; font-size:0.78rem; letter-spacing:2px;">
        PASTE A YOUTUBE URL ABOVE AND HIT ANALYZE
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="footer">
    <a href="{BMAC_URL}" target="_blank" class="bmac-btn">
        ☕ Buy me a coffee
    </a>
    <div class="footer-note">Built with Streamlit + Claude AI · Free to use</div>
</div>
""", unsafe_allow_html=True)
