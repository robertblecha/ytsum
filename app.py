import streamlit as st
import anthropic
import re
import json
import time
import urllib.request
from datetime import datetime, timezone

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="YT Summarizer", page_icon="▶", layout="wide")

BMAC_URL = "https://buymeacoffee.com/robertiscreating"

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0a0a0a; color: #f0f0f0; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; }

.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 2.5rem; font-weight: 700; color: #f0f0f0;
    letter-spacing: -1px; line-height: 1.1; margin-bottom: 0.3rem;
}
.subtitle { color: #555; font-size: 1.05rem; margin-bottom: 2rem; line-height: 1.6; }
.accent { color: #ff4d4d; }

.card { background: #141414; border: 1px solid #222; border-radius: 14px; padding: 1.6rem; margin-bottom: 1.2rem; }

.section-label {
    font-family: 'Space Mono', monospace; font-size: 0.68rem;
    letter-spacing: 3px; text-transform: uppercase; color: #ff4d4d; margin-bottom: 1rem;
}

.video-meta { margin-bottom: 1.4rem; padding-bottom: 1.2rem; border-bottom: 1px solid #1e1e1e; }
.video-title-display { font-size: 1.25rem; font-weight: 600; color: #f0f0f0; line-height: 1.4; margin-bottom: 0.4rem; }
.video-sub-meta { font-size: 0.88rem; color: #555; font-family: 'Space Mono', monospace; display: flex; gap: 1.2rem; flex-wrap: wrap; }
.video-sub-meta span { display: flex; align-items: center; gap: 0.3rem; }

.summary-text { font-size: 1.08rem; line-height: 1.85; color: #d8d8d8; font-weight: 500; }

.bullet-item { display: flex; gap: 0.9rem; padding: 0.7rem 0; border-bottom: 1px solid #1e1e1e; font-size: 1.08rem; color: #bbb; line-height: 1.7; }
.bullet-item:last-child { border-bottom: none; }
.bullet-dot { color: #ff4d4d; font-weight: 700; flex-shrink: 0; margin-top: 3px; }

.transcript-box { max-height: 380px; overflow-y: auto; font-size: 0.92rem; color: #777; line-height: 1.85; padding-right: 0.5rem; }
.transcript-box::-webkit-scrollbar { width: 4px; }
.transcript-box::-webkit-scrollbar-track { background: #0a0a0a; }
.transcript-box::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }

.answer-box { background: #0f0f0f; border-left: 3px solid #ff4d4d; padding: 1.1rem 1.4rem; border-radius: 0 10px 10px 0; font-size: 1.05rem; color: #bbb; line-height: 1.75; margin-top: 0.8rem; } .answer-box h1,.answer-box h2,.answer-box h3,.answer-box h4 { font-family: 'DM Sans', sans-serif !important; font-size: 1rem !important; font-weight: 600 !important; color: #d0d0d0; margin: 0.8rem 0 0.3rem 0; }

.progress-wrap { background: #141414; border: 1px solid #222; border-radius: 14px; padding: 1.2rem 1.6rem; }
.progress-step { display: flex; align-items: center; gap: 0.7rem; padding: 0.55rem 0; font-size: 0.95rem; border-bottom: 1px solid #1a1a1a; }
.progress-step:last-child { border-bottom: none; }
.step-icon { font-size: 1rem; width: 1.4rem; text-align: center; }
.progress-bar-wrap { margin-top: 0.8rem; background: #1a1a1a; border-radius: 4px; height: 4px; overflow: hidden; }
.progress-bar-fill { height: 4px; background: #ff4d4d; border-radius: 4px; }

.stats-row { display: flex; gap: 2rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.stat-item { text-align: left; }
.stat-number { font-family: 'Space Mono', monospace; font-size: 1.6rem; font-weight: 700; color: #ff4d4d; line-height: 1; }
.stat-label { font-size: 0.78rem; color: #555; margin-top: 0.2rem; letter-spacing: 1px; text-transform: uppercase; }

.feed-card {
    background: #111; border: 1px solid #1a1a1a; border-radius: 10px;
    padding: 0.8rem; display: flex; gap: 0.8rem; align-items: flex-start;
    margin-bottom: 0.6rem; transition: border-color 0.2s;
    text-decoration: none; color: inherit; cursor: pointer;
}
.feed-card:hover { border-color: #ff4d4d44; background: #161616; }
.feed-thumb { width: 88px; height: 50px; object-fit: cover; border-radius: 6px; flex-shrink: 0; background: #1a1a1a; }
.feed-title { font-size: 0.85rem; color: #ccc; line-height: 1.45; margin-bottom: 0.35rem; font-weight: 500; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.feed-meta { font-size: 0.73rem; color: #444; font-family: 'Space Mono', monospace; }

/* Share banner */
.share-banner {
    background: #111; border: 1px solid #2a2a2a; border-radius: 10px;
    padding: 0.8rem 1.2rem; display: flex; align-items: center; gap: 1rem;
    margin-bottom: 1.2rem; flex-wrap: wrap;
}
.share-url { font-family: 'Space Mono', monospace; font-size: 0.8rem; color: #666; flex: 1; word-break: break-all; }
.cached-badge { background: #1a2a1a; border: 1px solid #2a4a2a; color: #4caf50; font-family: 'Space Mono', monospace; font-size: 0.7rem; letter-spacing: 2px; padding: 0.25rem 0.6rem; border-radius: 4px; white-space: nowrap; }

.stTextInput > div > div > input { background: #141414 !important; border: 1px solid #2a2a2a !important; border-radius: 10px !important; color: #f0f0f0 !important; font-size: 1.08rem !important; padding: 0.65rem 1rem !important; }
.stTextInput > div > div > input:focus { border-color: #ff4d4d !important; box-shadow: 0 0 0 2px rgba(255,77,77,0.12) !important; }
.stFormSubmitButton > button { background: #ff4d4d !important; color: #fff !important; border: none !important; border-radius: 10px !important; font-family: 'Space Mono', monospace !important; font-size: 1.1rem !important; font-weight: 700 !important; letter-spacing: 2px !important; padding: 0.85rem 2.8rem !important; }
/* ASK button: secondary gray, match input height */
[data-testid="stForm"]:has([data-testid="stTextInput"]) .stFormSubmitButton > button { background: #1a1a1a !important; color: #aaa !important; border: 1px solid #2a2a2a !important; font-size: 0.85rem !important; font-weight: 400 !important; letter-spacing: 1px !important; padding: 0 1.2rem !important; height: 42px !important; min-height: 42px !important; }
[data-testid="stForm"]:has([data-testid="stTextInput"]) .stFormSubmitButton { display: flex !important; align-items: flex-end !important; }
[data-testid="stForm"]:has([data-testid="stTextInput"]) .stTextInput > div > div > input { height: 42px !important; min-height: 42px !important; box-sizing: border-box !important; }
.stButton > button:hover { opacity: 0.85 !important; }
/* Hide the invisible feed trigger buttons */
[data-testid="stButton"] button[title] { 
    position: absolute !important; opacity: 0 !important; pointer-events: none !important; width: 0 !important; height: 0 !important; padding: 0 !important; 
}
.stExpander { border: 1px solid #1e1e1e !important; border-radius: 12px !important; background: #141414 !important; }

.footer { margin-top: 4rem; padding: 2rem 0 1rem; border-top: 1px solid #1a1a1a; text-align: center; }
.bmac-btn { display: inline-flex; align-items: center; gap: 0.5rem; background: #FFDD00; color: #000 !important; text-decoration: none !important; padding: 0.65rem 1.5rem; border-radius: 10px; font-weight: 600; font-size: 0.92rem; transition: opacity 0.2s; }
.bmac-btn:hover { opacity: 0.85; }
.footer-note { color: #333; font-size: 0.75rem; margin-top: 0.9rem; font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ── Storage helpers (file-based, /tmp persists across sessions) ──────────────
import os, hashlib

STORAGE_DIR = "/tmp/ytsum_store"
os.makedirs(STORAGE_DIR, exist_ok=True)

def _key_path(key: str) -> str:
    safe = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(STORAGE_DIR, f"{safe}.json")

def storage_get(key: str) -> dict | None:
    try:
        path = _key_path(key)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def storage_set(key: str, value: dict):
    try:
        path = _key_path(key)
        with open(path, "w") as f:
            json.dump(value, f)
    except Exception:
        pass


# ── In-memory shared store for recent/stats (fast, server lifetime) ───────────
@st.cache_resource
def get_shared_store():
    # Try to load persisted feed on first boot
    persisted = None
    try:
        persisted = storage_get("feed:meta")
    except Exception:
        pass
    if persisted:
        return persisted
    return {"recent_videos": [], "total_count": 0, "total_words": 0}

shared = get_shared_store()


def persist_shared():
    storage_set("feed:meta", {
        "recent_videos": shared["recent_videos"],
        "total_count": shared["total_count"],
        "total_words": shared["total_words"],
    })


# ── Core helpers ──────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def get_video_info(video_id: str) -> dict:
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read())
            return {"title": data.get("title", "Unknown title"), "author": data.get("author_name", "Unknown")}
    except Exception:
        return {"title": "Unknown title", "author": "Unknown"}


def time_ago(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        if s < 60: return "just now"
        if s < 3600: return f"{s // 60}m ago"
        if s < 86400: return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return ""


def get_transcript(video_id: str) -> tuple[str, str]:
    from supadata import Supadata, SupadataError
    api_key = st.secrets.get("SUPADATA_API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing SUPADATA_API_KEY in Streamlit secrets.")
    sd = Supadata(api_key=api_key)
    try:
        result = sd.transcript(
            url=f"https://www.youtube.com/watch?v={video_id}",
            text=True,
            mode="native",
        )
        if not result or not getattr(result, "content", None):
            raise RuntimeError("No subtitles found for this video.")
        text = result.content if isinstance(result.content, str) else " ".join(c.text for c in result.content)
        lang = getattr(result, "lang", "unknown")
        return text, lang
    except SupadataError as e:
        raise RuntimeError(f"Transcript unavailable: {e}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error: {type(e).__name__}: {e}")



def get_claude_client():
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
        model="claude-opus-4-6", max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text
    summary, bullets = "", []
    if "SUMMARY:" in raw and "BULLETS:" in raw:
        summary = raw.split("BULLETS:")[0].replace("SUMMARY:", "").strip()
        bullets = [l.lstrip("- •").strip() for l in raw.split("BULLETS:")[1].strip().splitlines() if l.strip().startswith(("-", "•"))]
    else:
        summary = raw
    return {"summary": summary, "bullets": bullets}


def claude_answer(transcript: str, question: str) -> str:
    response = get_claude_client().messages.create(
        model="claude-opus-4-6", max_tokens=800,
        messages=[{"role": "user", "content": f"""Based on this YouTube video transcript, answer the user's question concisely and accurately. If the answer is not in the transcript, say so.

TRANSCRIPT:
{transcript[:12000]}

QUESTION: {question}"""}]
    )
    return response.content[0].text


def load_cached_analysis(video_id: str) -> dict | None:
    return storage_get(f"cache:{video_id}")


def save_cached_analysis(video_id: str, payload: dict):
    storage_set(f"cache:{video_id}", payload)


def add_to_recent(video_id: str, info: dict, word_count: int):
    entry = {
        "video_id": video_id,
        "title": info["title"],
        "author": info["author"],
        "thumb": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    videos = [v for v in shared["recent_videos"] if v.get("video_id") != video_id]
    videos.insert(0, entry)
    shared["recent_videos"] = videos[:20]
    shared["total_count"] += 1
    shared["total_words"] += word_count
    persist_shared()


def render_progress(placeholder, steps, pct):
    icons = {"done": "✅", "active": "⏳", "pending": "○"}
    colors = {"done": "#4caf50", "active": "#ff4d4d", "pending": "#333"}
    rows = "".join(
        f'<div class="progress-step"><span class="step-icon">{icons[s]}</span><span style="color:{colors[s]};font-size:0.95rem">{l}</span></div>'
        for l, s in steps
    )
    placeholder.markdown(f"""
    <div class="progress-wrap">
        <div class="section-label">Processing</div>
        {rows}
        <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)


# ── Query param handling ──────────────────────────────────────────────────────

params = st.query_params
qparam_vid = params.get("v", "")

# If ?v= is set and we haven't loaded it yet this session, auto-load from cache
if qparam_vid and st.session_state.get("loaded_vid") != qparam_vid:
    cached = load_cached_analysis(qparam_vid)
    if cached:
        st.session_state.update({
            "video_id": qparam_vid,
            "video_url": f"https://www.youtube.com/watch?v={qparam_vid}",
            "transcript": cached.get("transcript", ""),
            "lang": cached.get("lang", ""),
            "analysis": cached.get("analysis"),
            "video_info": cached.get("info"),
            "from_cache": True,
            "loaded_vid": qparam_vid,
        })
        st.rerun()


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">YT <span class="accent">//</span> Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Transcript · Summary · Q&A — for any YouTube video</div>', unsafe_allow_html=True)

with st.form(key="analyze_form", border=False):
    url_input = st.text_input(
        label="YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
        value=f"https://www.youtube.com/watch?v={qparam_vid}" if qparam_vid and st.session_state.get("from_cache") else "",
    )
    analyze_btn = st.form_submit_button("▶  ANALYZE")

# ── Analysis flow ─────────────────────────────────────────────────────────────

if analyze_btn and url_input:
    video_id = extract_video_id(url_input)
    if not video_id:
        st.error("Couldn't recognize YouTube URL. Try a different format.")
    else:
        # Check cache first
        cached = load_cached_analysis(video_id)
        if cached:
            st.session_state.update({
                "video_id": video_id,
                "video_url": url_input,
                "transcript": cached.get("transcript", ""),
                "lang": cached.get("lang", ""),
                "analysis": cached.get("analysis"),
                "video_info": cached.get("info"),
                "from_cache": True,
            })
            st.query_params["v"] = video_id
            st.rerun()
        else:
            st.session_state["from_cache"] = False
            st.markdown("---")
            prog = st.empty()

            render_progress(prog, [
                ("Fetching transcript from YouTube...", "active"),
                ("Analyzing with Claude AI...", "pending"),
            ], 15)

            try:
                transcript_text, lang = get_transcript(video_id)
                st.session_state.update({
                    "transcript": transcript_text, "video_url": url_input,
                    "video_id": video_id, "lang": lang, "analysis": None, "video_info": None,
                })
            except RuntimeError as e:
                prog.empty(); st.error(str(e)); st.stop()

            render_progress(prog, [
                ("Fetching transcript from YouTube...", "done"),
                ("Analyzing with Claude AI...", "active"),
            ], 55)

            try:
                analysis = claude_analyze(transcript_text, url_input)
                st.session_state["analysis"] = analysis
            except RuntimeError as e:
                prog.empty(); st.error(str(e)); st.stop()

            render_progress(prog, [
                ("Fetching transcript from YouTube...", "done"),
                ("Analyzing with Claude AI...", "done"),
            ], 100)

            info = get_video_info(video_id)
            st.session_state["video_info"] = info

            # Save to persistent cache
            save_cached_analysis(video_id, {
                "transcript": transcript_text,
                "lang": lang,
                "analysis": analysis,
                "info": info,
                "cached_at": datetime.now(timezone.utc).isoformat(),
            })

            # Update feed + stats
            add_to_recent(video_id, info, len(transcript_text.split()))

            # Set query param for shareable URL
            st.query_params["v"] = video_id

            time.sleep(0.4)
            prog.empty()
            st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────

if st.session_state.get("analysis"):
    st.markdown("---")
    analysis = st.session_state["analysis"]
    transcript_text = st.session_state["transcript"]
    video_id = st.session_state["video_id"]
    info = st.session_state.get("video_info") or {}
    from_cache = st.session_state.get("from_cache", False)

    share_url = f"https://jc6yjewlm4knn7dltaihlg.streamlit.app/?v={video_id}"
    cache_badge = '<span class="cached-badge">✓ CACHED</span>' if from_cache else ''
    title_display = info.get("title", "")
    author_display = info.get("author", "")
    lang_display = st.session_state.get("lang", "")

    # Title + share above columns
    _t_col, _s_col = st.columns([11, 1])
    with _t_col:
        st.markdown(
            f'<div style="font-size:1.7rem;font-weight:700;color:#f0f0f0;line-height:1.3;margin-bottom:0.4rem;">{title_display}</div>'
            f'<div style="font-size:0.88rem;color:#555;font-family:Space Mono,monospace;">&#128100; {author_display} &nbsp;&middot;&nbsp; &#127760; {lang_display}</div>'
            f'<div style="border-top:1px solid #1e1e1e;margin-top:1rem;"></div>',
            unsafe_allow_html=True
        )
    with _s_col:
        st.components.v1.html(
            '<button id="shareBtn" onclick="'
            "navigator.clipboard.writeText('" + share_url + "');"
            "var b=document.getElementById('shareBtn');"
            "b.innerHTML='<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'14\\' height=\\'14\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'#4caf50\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'><polyline points=\\'20 6 9 17 4 12\\'/></svg>Copied';"
            "b.style.borderColor='#2a4a2a';b.style.color='#4caf50';"
            "setTimeout(function(){"
            "b.innerHTML='<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'14\\' height=\\'14\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'#aaa\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'><circle cx=\\'18\\' cy=\\'5\\' r=\\'3\\'/><circle cx=\\'6\\' cy=\\'12\\' r=\\'3\\'/><circle cx=\\'18\\' cy=\\'19\\' r=\\'3\\'/><line x1=\\'8.59\\' y1=\\'13.51\\' x2=\\'15.42\\' y2=\\'17.49\\'/><line x1=\\'15.41\\' y1=\\'6.51\\' x2=\\'8.59\\' y2=\\'10.49\\'/></svg>Share Link';"
            "b.style.borderColor='#2a2a2a';b.style.color='#aaa';"
            "},2000);"
            '" title="Copy Share Link" '
            'style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:6px 10px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;color:#aaa;font-family:monospace;font-size:12px;white-space:nowrap;transition:all 0.2s;">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#aaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>'
            '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>'
            '</svg>Share Link</button>',
            height=45
        )
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(f"""
        <div style="border-radius:12px; overflow:hidden; margin-bottom:1.2rem;">
            <iframe width="100%" height="315" src="https://www.youtube.com/embed/{video_id}"
            frameborder="0" allowfullscreen style="display:block;"></iframe>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Ask a question about this video</div>', unsafe_allow_html=True)
        with st.form(key="ask_form", border=False):
            q_col, btn_col = st.columns([5, 1])
            with q_col:
                question = st.text_input("Question", placeholder="What does it say about...?", label_visibility="collapsed", key="question_input")
            with btn_col:
                ask_btn = st.form_submit_button("ASK")

        if ask_btn and question:
            with st.spinner("Finding the answer..."):
                answer = claude_answer(transcript_text, question)
            st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""
        <div class="card">
            <div class="section-label">Summary</div>
            <div class="summary-text"><strong>{analysis["summary"]}</strong></div>
        </div>
        """, unsafe_allow_html=True)

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

# ── Recent videos feed ────────────────────────────────────────────────────────

st.markdown("---")
recent = shared.get("recent_videos", [])
total_count = shared.get("total_count", 0)
total_minutes = shared.get("total_words", 0) // 130

if recent:
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-item"><div class="stat-number">{total_count}</div><div class="stat-label">Videos analyzed</div></div>
        <div class="stat-item"><div class="stat-number">{total_minutes:,}</div><div class="stat-label">Minutes of content</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Recently summarized</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, v in enumerate(recent[:10]):
        with cols[i % 2]:
            ago = time_ago(v.get("timestamp", ""))
            vid_id = v["video_id"]
            st.markdown(f"""
            <a href="/?v={vid_id}" style="text-decoration:none;display:block;">
            <div class="feed-card">
                <img class="feed-thumb" src="{v['thumb']}" onerror="this.style.background='#1a1a1a'"/>
                <div style="min-width:0">
                    <div class="feed-title">{v['title']}</div>
                    <div class="feed-meta">👤 {v.get('author','')} &nbsp;·&nbsp; {ago}</div>
                </div>
            </div>
            </a>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center;color:#222;padding:2rem 0;font-family:'Space Mono',monospace;font-size:0.75rem;letter-spacing:2px;">
        NO VIDEOS SUMMARIZED YET — BE THE FIRST
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.get("analysis") and not analyze_btn:
    st.markdown("""
    <div style="text-align:center;color:#1e1e1e;padding:2rem 0;font-family:'Space Mono',monospace;font-size:0.75rem;letter-spacing:2px;">
        PASTE A YOUTUBE URL ABOVE AND HIT ANALYZE
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    <a href="{BMAC_URL}" target="_blank" class="bmac-btn">☕ Buy me a coffee</a>
    <div class="footer-note">Built with Streamlit + Claude AI · Free to use</div>
</div>
""", unsafe_allow_html=True)
