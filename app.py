# pyright: reportUndefinedVariable=false

import os
import re
import base64
import html as _html
import hashlib
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

if "img_value" not in st.session_state:
    st.session_state.img_value = None


# ------------------ 0) Setup ------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY", "")
if API_KEY:
    genai.configure(api_key=API_KEY)

st.set_page_config(page_title="AI UI Designer", page_icon="🎨", layout="wide")
st.title("GenWebly")
st.caption("Prompt it. Build it.")

# Session state
init_vals = {
    "html": "",
    "raw_html": "",
    "regen_notes": "",
    "last_img_mode": None,
    "last_img_value": "",
    "last_prompt": "",
    "stack_langs": [],
    "show_learn": False,
    "stack_js_mode": "Static",
    "stack_js_use": "",
    "stack_choice": "— choose —",
    "stack_prev_choice": "— choose —",
    "render_tick": 0,

}
for k, v in init_vals.items():
    if k not in st.session_state:
        st.session_state[k] = v
if "render_tick" not in st.session_state:
    st.session_state["render_tick"] = 0


# ------------------ 1) Theme helpers ------------------
def theme_palette(prompt_text: str) -> dict:
    p = (prompt_text or "").lower()

    def pal(bg, bg2, text, muted, primary, accent, border):
        return {
            "bg": bg,
            "bg2": bg2,
            "text": text,
            "muted": muted,
            "primary": primary,
            "accent": accent,
            "border": border,
        }

    if any(k in p for k in ["wedding", "love", "invite", "bride", "groom"]):
        return pal("#fff7fb", "#fdeef4", "#2d1f24", "#7a6a70", "#d9c06d", "#f4b6c2", "#ead9b0")
    if any(k in p for k in ["tech", "ai", "cyber", "startup", "saas"]):
        return pal("#0b0f1a", "#141a2a", "#e6f0ff", "#9db2ce", "#7b2ff7", "#00f0ff", "#27304a")
    if any(k in p for k in ["coffee", "cafe", "bakery", "espresso"]):
        return pal("#fff8f0", "#f3e5d8", "#2b211a", "#7a5c49", "#b36a3c", "#d2a679", "#e2c8ad")
    if any(k in p for k in ["fashion", "style", "boutique"]):
        return pal("#fffafc", "#fde8f2", "#1f1a1d", "#846877", "#f472b6", "#facc15", "#eed4e1")
    if any(k in p for k in ["portfolio", "resume", "personal"]):
        return pal("#f6f7fb", "#e9edfb", "#0f172a", "#4b5563", "#6366f1", "#22d3ee", "#c7d2fe")
    if any(k in p for k in ["travel", "beach", "adventure", "tour"]):
        return pal("#f1fbff", "#e6faff", "#0b2a3a", "#4b6b7a", "#38bdf8", "#fbbf24", "#cfe9f6")
    return pal("#faf6ff", "#e7f1ff", "#0f172a", "#64748b", "#8b5cf6", "#22d3ee", "#dbeafe")


def build_theme_css(p: dict) -> str:
    return f"""
<style>
:root {{
  --bg: {p['bg']};
  --bg2: {p['bg2']};
  --text: {p['text']};
  --muted: {p['muted']};
  --primary: {p['primary']};
  --accent: {p['accent']};
  --border: {p['border']};
}}
html, body {{
  background: radial-gradient(1200px 700px at 20% 0%, var(--bg2), var(--bg));
  color: var(--text);
}}
section, .card, .panel, .feature {{
  background: rgba(255,255,255,0.6);
  backdrop-filter: blur(6px);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1.25rem; margin: .75rem 0;
}}
#hero {{
  min-height: 70vh; display: flex; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
}}
h1, h2, h3 {{ color: var(--text); letter-spacing: .3px; text-shadow: 0 1px 0 rgba(255,255,255,.25); }}
a, .link {{ color: var(--primary); text-decoration: none; }}
a:hover {{ opacity: .9; }}
button, .btn, .cta, input[type="submit"] {{
  display: inline-block; padding: .75rem 1.1rem; border-radius: 12px;
  border: 1px solid var(--border);
  background: linear-gradient(180deg, var(--primary), var(--accent));
  color: #0d0f12; font-weight: 600; cursor: pointer;
  transition: transform .08s ease, box-shadow .18s ease;
  box-shadow: 0 6px 20px rgba(0,0,0,.12);
}}
button:hover, .btn:hover, .cta:hover, input[type="submit"]:hover {{ transform: translateY(-2px); }}
nav a {{ padding: .35rem .6rem; border-radius: 8px; }}
hr {{ border: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); }}
</style>
"""


def theme_aware_svg(prompt_text: str) -> str:
    p = (prompt_text or "").lower()
    if any(k in p for k in ["wedding", "love", "invite"]):
        color1, color2, shape = "#f4b6c2", "#ffd6e0", "roses and cherry blossoms"
    elif any(k in p for k in ["tech", "ai", "cyber", "startup"]):
        color1, color2, shape = "#00f0ff", "#7b2ff7", "circuit lines and neon glow"
    elif any(k in p for k in ["coffee", "cafe", "bakery"]):
        color1, color2, shape = "#b6905b", "#f5deb3", "coffee cups and steam"
    elif any(k in p for k in ["fashion", "style", "boutique"]):
        color1, color2, shape = "#f9a8d4", "#fcd34d", "flowing fabric ribbons"
    elif any(k in p for k in ["portfolio", "resume", "personal"]):
        color1, color2, shape = "#60a5fa", "#a78bfa", "abstract geometric polygons"
    elif any(k in p for k in ["travel", "beach", "adventure"]):
        color1, color2, shape = "#38bdf8", "#facc15", "waves and airplane trails"
    else:
        color1, color2, shape = "#e0c3fc", "#8ec5fc", "soft pastel sparkles"
    return f"""
<svg id="theme-art" viewBox="0 0 220 220" width="240" height="240"
     style="position:absolute;top:-10px;left:-10px;opacity:.15;z-index:0;pointer-events:none;">
  <defs>
    <linearGradient id="grad1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{color1}"/><stop offset="1" stop-color="{color2}"/>
    </linearGradient>
  </defs>
  <g fill="url(#grad1)" stroke="{color2}" stroke-width="0.6">
    <path d="M40,110 C60,80 90,70 120,70 C145,70 170,80 185,95
             C130,125 90,150 55,170 C35,150 25,130 40,110 Z"/>
    <text x="12" y="205" font-size="10" fill="{color2}" opacity=".6">{shape}</text>
  </g>
</svg>
"""


def detect_visual_intent(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    keywords = [
        "flowers",
        "floral",
        "cloud",
        "butterfly",
        "sparkle",
        "glow",
        "neon",
        "pattern",
        "illustration",
        "icons",
        "waves",
        "palm",
        "bokeh",
        "confetti",
        "cherries",
        "stars",
        "gradient background",
        "texture",
        "grid",
        "circuit",
    ]
    return any(k in t for k in keywords)


# ------------------ 2) HTML safety + postprocess ------------------
def sanitize_html(raw: str) -> str:
    html = (raw or "").replace("```html", "").replace("```", "").strip()
    if not html:
        return ""
    html = re.sub(r'href="/[^"]*"', 'href="#"', html)
    html = html.replace('href="/"', 'href="#"')

    def add_target_blank(m):
        url = m.group(1)
        return f'href="{url}" target="_blank" rel="noopener noreferrer"'

    html = re.sub(r'href="(https?://[^"]+)"(?![^>]*\\btarget=)', add_target_blank, html)

    interceptor = """
<script>
document.addEventListener('click', function(e){
  const a = e.target.closest('a'); if(!a) return;
  const href = a.getAttribute('href') || '';
  if (href.startsWith('#')) return;
  if (/^https?:\\/\\//i.test(href) && a.target === '_blank') return;
  e.preventDefault();
  if (href === '#' || href === '') window.scrollTo({top: 0, behavior: 'smooth'});
});
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click', function(ev){
    const id = this.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if(el){ ev.preventDefault(); el.scrollIntoView({behavior:'smooth'}); }
  });
});
</script>
"""
    if "</body>" in html:
        html = html.replace("</body>", interceptor + "</body>")
    else:
        html += interceptor
    return html

extra_image_src = st.session_state.get("img_value", "")
image_place_hint = st.session_state.get("image_place_hint", "")


def postprocess_html(raw_html: str, hero_image_url: str = "", ensure_story_anchor: bool = True, prompt_text: str = "") -> str:
    html = (raw_html or "").replace("```html", "").replace("```", "").strip()
    if "<html" not in html.lower():
        html = f"<html><head></head><body>{html}</body></html>"

    palette = theme_palette(prompt_text)
    theme_css = build_theme_css(palette)
    if "</head>" in html:
        html = html.replace("</head>", theme_css + "</head>")
    else:
        html = theme_css + html

    html = re.sub(r'href="/[^"]*"', 'href="#"', html)
    html = html.replace('href="/"', 'href="#"')
    if ensure_story_anchor and "#story" in html:
        html = html.replace('href="#"', 'href="#story"')

    def _add_target_blank(m):
        url = m.group(1)
        return f'href="{url}" target="_blank" rel="noopener noreferrer"'

    html = re.sub(r'href="(https?://[^"]+)"(?![^>]*\\btarget=)', _add_target_blank, html)

    if hero_image_url and "hero background" in prompt_text.lower():

        css = "<style>#hero{background:url('" + hero_image_url + "') center/cover no-repeat;}</style>"
        html = html.replace("</head>", css + "</head>") if "</head>" in html else css + html

        # --- CONDITIONAL SPARKLES ENGINE ---
    user_hates_sparkles = "no sparkle" in prompt_text.lower() or \
                          "remove sparkle" in prompt_text.lower() or \
                          "remove sparkles" in prompt_text.lower() or \
                          "remove snow" in prompt_text.lower() or \
                          "remove floating" in prompt_text.lower()

    sparkle_keywords = ["sparkle", "sparkles", "glow", "neon", "bokeh", "confetti", "dreamy", "magic", "fairy"]

    user_wants_sparkles = any(k in prompt_text.lower() for k in sparkle_keywords)

    # Remove sparkles fully if user said no
    if user_hates_sparkles:
        html = re.sub(r'<style>[\s\S]*?#sparkles[\s\S]*?</script>', '', html)
        return html

    # Add sparkles only if requested
    if user_wants_sparkles and 'id="sparkles"' not in html:
        sparkles = """
        <style>
        #sparkles{position:fixed;inset:0;pointer-events:none;z-index:1;}
        .sparkle{position:absolute;border-radius:50%;
        background:radial-gradient(circle, rgba(255,255,255,0.9), rgba(255,255,255,0));
        opacity:.6;filter:blur(.5px);animation:float 6s linear infinite;}
        @keyframes float{from{transform:translateY(0)}to{transform:translateY(-120vh)}}
        </style>
        <div id="sparkles"></div>
        <script>(function(){const c=document.getElementById('sparkles');if(!c)return;
        for(let i=0;i<28;i++){const s=document.createElement('div');s.className='sparkle';
        const d=3+Math.random()*7;s.style.width=d+'px';s.style.height=d+'px';
        s.style.left=Math.random()*100+'vw';s.style.top=(100+Math.random()*40)+'vh';
        s.style.animationDelay=(Math.random()*6)+'s';
        s.style.animationDuration=(5+Math.random()*6)+'s';c.appendChild(s);}})();</script>
        """
        html = html.replace("</body>", sparkles + "</body>") if "</body>" in html else html + sparkles

    if 'id="theme-art"' not in html:
        html = html.replace("<body>", "<body>" + theme_aware_svg(prompt_text))

    return html


 





# ------------------ 3) Stack helpers + prompt builders ------------------
ALL_LANGS = ["HTML", "CSS", "JS", "Tailwind", "Bootstrap", "jQuery"]


def check_stack_applicability(selected):
    """Return (is_applicable: bool, message: str)."""
    if not selected:
        return True, "No stack chosen; model will pick a reasonable default (HTML + CSS)."
    if "HTML" not in selected:
        return False, "Stack not applicable: HTML is required since the output is always an HTML document. Add 'HTML'."
    if "Tailwind" in selected and "Bootstrap" in selected:
        return False, "Stack not applicable: Tailwind CSS and Bootstrap are full CSS frameworks that often conflict; pick one of them, not both."
    return True, "Stack applicable."


def build_stack_rules(selected_langs, js_mode: str, js_use: str) -> str:
    if not selected_langs:
        return ""

    langs = set(selected_langs)
    rules = []

    # Base HTML/CSS rules
    if "HTML" in langs and "CSS" not in langs and not (langs & {"Tailwind", "Bootstrap"}):
        rules.append("Output a single self-contained HTML file. Use minimal inline CSS inside a <style> block.")
    if "HTML" in langs and "CSS" in langs and not (langs & {"Tailwind", "Bootstrap", "jQuery"}):
        rules.append("Use a single HTML file with a <style> block for CSS. Avoid external libraries.")

    # Tailwind
    if "Tailwind" in langs:
        rules.append("Use Tailwind utility classes. Include CDN <script src='https://cdn.tailwindcss.com'></script> in <head>.")

    # Bootstrap
    if "Bootstrap" in langs:
        rules.append("Use Bootstrap 5 via CDN (CSS and JS). Build layout with Bootstrap components.")

    # jQuery
    has_js_like = False
    if "jQuery" in langs:
        rules.append("Include jQuery via CDN and use it for small interactions.")
        has_js_like = True

    # Vanilla JS / Bootstrap behavior
    if "JS" in langs or "Bootstrap" in langs:
        has_js_like = True

    if has_js_like:
        rules.append("All code must live in a single HTML file with <style> and <script> blocks.")
        if js_mode == "Dynamic":
            rules.append(
                "Use JavaScript to add interactivity (tabs, modals, form handling, smooth scrolling, localStorage, etc.). Avoid external API requests."
            )
        else:
            rules.append("Keep JavaScript minimal, so the page mostly behaves like a static site (minor enhancements only).")
        if js_use.strip():
            rules.append(f"Specific JavaScript behavior requested by the user: {js_use.strip()}")

    return "\n".join(rules)


def build_revision_prompt(
    current_html: str,
    stack_rules: str,
    change_list: str = "",
    extra_image_src: str = "",
    image_place_hint: str = "",
    svg_hint: str = "",
    logic_fixes: str = "",
):
    rules = [
    "Revise the EXISTING HTML below. Do NOT recreate from scratch.",
    "APPLY ONLY the requested changes. Do not remove sections or anchors.",
    "Return ONE full HTML document (no markdown).",
    "IMPORTANT: If a change mentions color, font, placement, or logic, edit the exact CSS/JS/HTML selectors.",
    "Insert an HTML comment per applied change like <!--applied: change-key-->.",
    "Keep responsiveness and accessibility intact.",
    "YOU MUST make at least one visible modification to the HTML, even if the request is minor.",
]


    if stack_rules:
        rules.append("Respect these stack rules:\n" + stack_rules)

    # Make sure Gemini ALWAYS applies changes
    if change_list.strip():
        change_list += "\nALWAYS MODIFY AT LEAST ONE ELEMENT."

    if change_list.strip():
        rules.append("Apply these changes:\n" + change_list.strip())
    else:
        rules.append("User gave no changes → apply gentle improvements only.")

    if logic_fixes.strip():
        rules.append("Logic fixes:\n" + logic_fixes.strip())

    if extra_image_src and image_place_hint:
        rules.append(
            f"PLACE THIS IMAGE EXACTLY at '{image_place_hint}'. USE THIS SRC ONLY: {extra_image_src}."
        )

    if svg_hint.strip():
        rules.append("Add inline SVG art: " + svg_hint.strip())

    return (
        "\n".join(rules)
        + "\n\n--- CURRENT HTML (EDIT THIS, DO NOT REWRITE) ---\n"
        + current_html
    )



# ------------------ 4) Helper utilities for regenerate verification/patch + splitting ------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _hash(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def ensure_min_date_js(html: str) -> str:
    snippet = """
<script>
(function(){
  function todayStr(){
    const t=new Date();
    const m=String(t.getMonth()+1).padStart(2,'0');
    const d=String(t.getDate()).padStart(2,'0');
    return `${t.getFullYear()}-${m}-${d}`;
  }
  document.querySelectorAll('input[type="date"]').forEach(el=>{
    const td=todayStr();
    if(!el.min) el.min = td;
    if(el.value && el.value < td) el.value = td;
    el.addEventListener('change',()=>{ if(el.value < td) el.value = td; });
  });
})();
</script>
"""
    return html.replace("</body>", snippet + "</body>") if "</body>" in html else (html + snippet)


def force_contact_text_black(html: str) -> str:
    style = """
<style id="contact-enforce-text">
#contact, section#contact, .contact, .contact-section { color:#000 !important; }
#contact p, .contact p, #contact li, .contact li { color:#000 !important; }
</style>
"""
    return html.replace("</head>", style + "</head>") if "</head" in html else (style + html)

# --- IMAGE INJECTION ENGINE (FINAL PATCH) ---
def apply_explicit_image_patch(html, src, place_hint, prompt):
    place_hint = (place_hint or "").lower()
    prompt = (prompt or "").lower()

    
    # Build <img> tag with size + opacity rules
    # Base styles so image is ALWAYS visible
    # --- FORCE IMAGE TO RENDER VISIBLY ---
    base_styles = [
    "width:100%",
    "height:100%",
    "object-fit:contain",
    "display:block"
]

# Optional size hints
    if "small" in place_hint:
        base_styles.append("max-width:90px")
    elif "medium" in place_hint:
        base_styles.append("max-width:180px")
    elif "large" in place_hint:
        base_styles.append("max-width:260px")

# Optional opacity
    m = re.search(r"opacity\s*([0-9]*\.?[0-9]+)", place_hint)
    if m:
        try:
            op = float(m.group(1))
            if op > 1:
                op = op / 100
            base_styles.append(f"opacity:{op}")
        except:
            pass

    style_attr = ' style="' + ";".join(base_styles) + ';"'

    img_tag = f'<img src="{src}" loading="lazy"{style_attr} />'



    # Placement logic
    # 1) CONTACT SECTION
    if "contact" in place_hint:
        return re.sub(
        r'(<section[^>]*id=["\']contact["\'][^>]*>)(.*?)(</section>)',
        r'\1' + img_tag + r'\3',
        html,
        flags=re.I | re.S
    )

    # 2) ABOUT SECTION
    if "about" in place_hint:
        return re.sub(
        r'(<section[^>]*id=["\']about["\'][^>]*>)(.*?)(</section>)',
        r'\1' + img_tag + r'\3',
        html,
        flags=re.I | re.S
    )


    # 3) HERO IMAGE — REPLACE CONTENT
    if "hero" in place_hint:
        return re.sub(
            r'(<section[^>]*id=["\']hero["\'][^>]*>)(.*?)(</section>)',
            r'\1' + img_tag + r'\3',
            html,
            flags=re.I | re.S
    )


    # 4) BOTTOM LEFT
    if "bottom left" in place_hint:
        fixed = (
            "<div style='position:absolute;left:0;bottom:0;z-index:50;'>"
            + img_tag +
            "</div>"
        )
        return html.replace("</body>", fixed + "</body>")

    # 5) BOTTOM RIGHT
    if "bottom right" in place_hint:
        fixed = (
            "<div style='position:absolute;right:0;bottom:0;z-index:50;'>"
            + img_tag +
            "</div>"
        )
        return html.replace("</body>", fixed + "</body>")

    # 6) DEFAULT — append before </body>
    return html.replace("</body>", img_tag + "</body>")

def inject_edit_delete_svgs_if_missing(html: str) -> str:
    add_svg_js = """
<script>
(function(){
  const editSVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zm14.71-9.04a1 1 0 0 0 0-1.41l-2.51-2.51a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 2-1.66z"/></svg>';
  const delSVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>';
  document.querySelectorAll('.icon-edit').forEach(el=>{ if(!el.innerHTML.trim()) el.innerHTML = editSVG; });
  document.querySelectorAll('.icon-delete').forEach(el=>{ if(!el.innerHTML.trim()) el.innerHTML = delSVG; });
})();
</script>
"""
    return html.replace("</body>", add_svg_js + "</body>") if "</body" in html else (html + add_svg_js)


def split_html_assets(raw_html: str):
    """Split raw HTML into index.html, styles.css, script.js."""
    html = (raw_html or "").strip()
    if not html:
        return "", "", ""

    css_parts = re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S | re.I)
    js_parts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.S | re.I)

    css = "\n\n".join(part.strip() for part in css_parts if part.strip())
    js = "\n\n".join(part.strip() for part in js_parts if part.strip())

    html_wo_css = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
    html_clean = re.sub(r"<script[^>]*>.*?</script>", "", html_wo_css, flags=re.S | re.I)

    inject = ""
    if css:
        inject += '<link rel="stylesheet" href="styles.css"/>\n'
    if js:
        inject += '<script src="script.js"></script>\n'

    if "</head>" in html_clean:
        html_clean = html_clean.replace("</head>", inject + "</head>")
    else:
        html_clean = inject + html_clean

    return html_clean.strip(), css.strip(), js.strip()


with st.expander("Choose stack (optional)", expanded=False):
    if "stack_langs" not in st.session_state:
        st.session_state["stack_langs"] = []

    selected = st.multiselect(
        "Languages / libraries",
        ALL_LANGS,
        default=st.session_state["stack_langs"],
        key="stack_langs_widget",
    )

    st.session_state["stack_langs"] = selected

    applicable, stack_msg = check_stack_applicability(selected)
    if applicable:
        st.markdown(
            f"<p style='font-size:0.85rem;font-style:italic;color:#9ca3af;'>*{stack_msg}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<p style='font-size:0.85rem;font-style:italic;color:#f97373;'>*{stack_msg}</p>",
            unsafe_allow_html=True,
        )

    # JS behavior controls only if JS or jQuery are present
    has_js_like = any(l in selected for l in ["JS", "jQuery"])
    if has_js_like:
        st.markdown("**Behavior for JS-based parts**")
        st.session_state["stack_js_mode"] = st.radio(
            "If JS is involved, should it be…",
            ["Static", "Dynamic"],
            index=0 if st.session_state["stack_js_mode"] == "Static" else 1,
            horizontal=True,
            key="stack_js_mode_radio",
        )
        st.session_state["stack_js_mode"] = st.session_state["stack_js_mode_radio"]
        st.session_state["stack_js_use"] = st.text_input(
            "(Optional) What should JS do?",
            value=st.session_state["stack_js_use"],
            placeholder="tabs, modal, localStorage diary, form validation…",
        )

 # --- Clean Small Learn More Button (Working Popover) ---
c1, c2 = st.columns([1, 4])
with c1:
    with st.popover("Learn more"):
        st.markdown("### Stack Languages Overview")
        st.write(
            """
**HTML** – structure of the page  
**CSS** – styles and layout  
**JS** – interactivity and logic  
**Tailwind** – utility-first CSS  
**Bootstrap** – prebuilt responsive components  
**jQuery** – older helper library for JavaScript  
"""
        )
with c2:
    st.caption("Quick overview of what each language/framework does.")
   




# JS mode/use from state
js_mode = st.session_state.get("stack_js_mode", "Static")
js_use = st.session_state.get("stack_js_use", "")

# ------------------ prompt + image inputs ------------------
prompt = st.text_area(
    "Describe your website",
    height=160,
    placeholder="e.g., reminder app with localStorage; no past dates; edit/delete with inline SVG icons; contact text must be black.",
)

col1, col2 = st.columns([2, 1])
with col1:
    bg_url = st.text_input("Background image URL (optional)", placeholder="https://example.com/your-image.jpg")
with col2:
    uploaded = st.file_uploader("Or upload an image", type=["png", "jpg", "jpeg"])

hint_text = st.text_input(
    "If no image URL/upload, give an image hint (AI will draw an inline SVG)",
    placeholder="pastel watercolor clouds and sparkles",
)


def file_to_data_url(file) -> str:
    if not file:
        return ""
    data = file.read()
    ext = file.name.split(".")[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode("utf-8")


# Decide image mode/value from inputs
img_mode, img_value = None, None
if bg_url:
    img_mode, img_value = "url", bg_url.strip()
elif uploaded:
    img_mode, img_value = "data", file_to_data_url(uploaded)
elif hint_text:
    img_mode, img_value = "svg", hint_text.strip()
else:
    if detect_visual_intent(prompt):
        img_mode, img_value = "svg", prompt.strip()

def build_prompt(u: str, img_mode=None, img_hint=None, stack_rules: str = "", temperature: float = 0.8) -> str:
    base = (
        "Return ONE complete HTML document (no markdown). "
        "Prefer a single file with inline <style> and optional <script>. "
        "Make it responsive and accessible with good contrast.\n"
        "STRUCTURE: header/nav, hero, 3 feature cards/sections, footer.\n"
        "NAV: in-page anchors only (e.g., href=\"#about\"). Smooth scrolling.\n"
        "Buttons/links: External links target='_blank' rel='noopener noreferrer'.\n"
        "Forms: no external navigation.\n"
    )
    if stack_rules:
        base += f"\nStack rules:\n{stack_rules}\n"

    if img_mode in ("data", "url"):
        base += "Use the user's provided image as the main hero background. Do not include other images.\n"
    elif img_mode == "svg" or (img_hint and img_hint.strip()):
        base += "Generate visuals as inline SVG or CSS drawings that match the hint. No external URLs.\n" + f"Image Hint: {img_hint}\n"
    else:
        base += "Do NOT include external <img> unless asked. Use gradients/SVG if visuals are needed.\n"

    return f"{base}\nUser request:\n{u}\n(temperature={temperature})"

# ------------------ 6) Generate ------------------
if st.button("Generate", type="primary"):
    if not API_KEY:
        st.session_state["html"] = "<html><body><h2>❌ No API key found in .env</h2></body></html>"
    else:
        with st.spinner("✨ Designing with Gemini..."):
            try:
                applicable, _msg = check_stack_applicability(st.session_state["stack_langs"])
                effective_langs = st.session_state["stack_langs"] if applicable else []
                stack_rules = build_stack_rules(effective_langs, js_mode, js_use)

                model = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    generation_config={"temperature": 0.8},
                )
                req = build_prompt(
                    prompt or "minimal landing page",
                    img_mode=img_mode,
                    img_hint=(img_value if img_mode == "svg" else None),
                    stack_rules=stack_rules,
                    temperature=0.8,
                )
                resp = model.generate_content(req)
                html = (resp.text or "").strip()
                st.session_state["raw_html"] = html
                safe = sanitize_html(html)

                # 🔴 ADD THIS BLOCK (IMAGE INSERTION)
                if img_mode in ("url", "data"):
                    safe = apply_explicit_image_patch(
                        safe,
                        img_value,
                        "",  # no place hint during initial generate
                        prompt
    )

                safe = postprocess_html(
                    safe,
                    hero_image_url="",  # IMPORTANT: prevent hero auto-bg
                    prompt_text=prompt,
)

                st.session_state["html"] = safe

                st.session_state["last_img_mode"] = img_mode
                st.session_state["last_img_value"] = img_value or ""
                st.session_state["last_prompt"] = prompt or "minimal landing page"
            except Exception as e:
                st.session_state["html"] = f"<html><body><h2>🚫 API Error</h2><pre>{e}</pre></body></html>"
                st.session_state["render_tick"] += 1


# ------------------ 7) Preview (device frames + Source with split option) ------------------
tab1, tab2 = st.tabs(["Preview", "Source"])
with tab1:
    st.markdown("### Preview")
    st.info(
    "**Live Preview Notice**\n\n"
    "The current preview reflects the latest generated layout and structure.\n\n"
    "• Some regenerated changes may require a refresh to fully apply.\n"
    "• Advanced image placement (precise box targeting) is actively being refined and will be enabled shortly.\n\n"
    "The exported source code remains correct and production-ready.",
    icon="ℹ️"
)


    # --- DEVICE SELECTION ---
    device = st.radio(
        "Device",
        ["Mobile", "Tablet", "Laptop", "Desktop"],
        horizontal=True,
    )

    # --- WIDTH MAPPING ---
    if device == "Mobile":
        w = 375
    elif device == "Tablet":
        w = 768
    elif device == "Laptop":
        w = 1280
    else:
        w = 1440

    height_px = st.slider("Frame height", 600, 1400, 900, 50)

    # --- PREVIEW RENDER ---
    preview_html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>
        body {{
          margin: 0;
          padding: 24px 12px;
          background: #0b0f1a;
          font-family: system-ui, -apple-system, Segoe UI, Roboto;
        }}
        .frame {{
          width: {w}px;
          height: {height_px}px;
          margin: 0 auto;
          border-radius: 18px;
          border: 1px solid rgba(120,130,150,.35);
          box-shadow: 0 20px 60px rgba(0,0,0,.18);
          overflow: auto;
          background: #fff;
        }}
      </style>
    </head>
    <body>
      <div class="frame">
        {st.session_state.get("html", "")}
      </div>
    </body>
    </html>
    """

    st.components.v1.html(preview_html, height=height_px + 100, scrolling=True)





with tab2:
    src_mode = st.radio(
        "Source view",
        ["Single HTML file", "HTML / CSS / JS"],
        horizontal=True,
    )

    if src_mode == "Single HTML file":
        st.code(st.session_state["html"], language="html")
        if st.session_state["html"]:
            st.download_button(
                "Download single HTML",
                st.session_state["html"].encode("utf-8"),
                "generated.html",
                "text/html",
            )
    else:
        raw_src = st.session_state.get("raw_html") or st.session_state["html"]
        html_main, css_code, js_code = split_html_assets(raw_src)

        if html_main:
            st.markdown("**index.html**")
            st.code(html_main, language="html")
        if css_code:
            st.markdown("**styles.css**")
            st.code(css_code, language="css")
        if js_code:
            st.markdown("**script.js**")
            st.code(js_code, language="javascript")

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        if html_main:
            with col_dl1:
                st.download_button(
                    "Download index.html",
                    html_main.encode("utf-8"),
                    "index.html",
                    "text/html",
                )
        if css_code:
            with col_dl2:
                st.download_button(
                    "Download styles.css",
                    css_code.encode("utf-8"),
                    "styles.css",
                    "text/css",
                )
        if js_code:
            with col_dl3:
                st.download_button(
                    "Download script.js",
                    js_code.encode("utf-8"),
                    "script.js",
                    "application/javascript",
                )

# ------------------ Regenerate (FINAL) ------------------
if st.session_state.get("html"):
    st.markdown("---")
    st.subheader("Regenerate / Apply Changes")

    regen_notes = st.text_area(
        "Describe the changes you want",
        height=140,
        placeholder="e.g. make buttons gold, place image near title as logo, remove hero image",
    )

    extra_image_upload = st.file_uploader(
        "(Optional) Upload / replace image",
        type=["png", "jpg", "jpeg"],
        key="regen_image",
    )

    image_place_hint = st.text_input(
        "(Optional) Where should the image be placed?",
        placeholder="e.g. small square logo near title, opacity 0.8",
    )

    do_regen = st.button("Regenerate")

    if do_regen and API_KEY:
        with st.spinner("Regenerating..."):
            try:
                # --- stack rules ---
                applicable, _ = check_stack_applicability(st.session_state["stack_langs"])
                stack_rules = build_stack_rules(
                    st.session_state["stack_langs"] if applicable else [],
                    js_mode,
                    js_use,
                )

                # --- model ---
                model = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    generation_config={"temperature": 0.25},
                )

                # --- source HTML ---
                current_html = (
                    st.session_state.get("raw_html")
                    or st.session_state.get("html")
                    or "<html><body></body></html>"
                )

                # --- revision prompt ---
                req = build_revision_prompt(
                    change_list=regen_notes,
                    current_html=current_html,
                    stack_rules=stack_rules,
                    extra_image_src="",
                    image_place_hint="",
                    svg_hint="",
                    logic_fixes="",
                )

                resp = model.generate_content(req)
                new_html = (resp.text or "").strip()

                # --- save raw ---
                st.session_state["raw_html"] = new_html

                # --- sanitize ---
                safe = sanitize_html(new_html)

                # --- image patch (ONLY if user uploaded + placement given) ---
                if extra_image_upload and image_place_hint:
                    img_src = file_to_data_url(extra_image_upload)
                    safe = apply_explicit_image_patch(
                        safe,
                        img_src,
                        image_place_hint,
                        st.session_state.get("last_prompt", ""),
                    )

                # --- final postprocess ---
                safe = postprocess_html(
                    safe,
                    hero_image_url="",  # ❗ DO NOT FORCE HERO IMAGE
                    prompt_text=(
                        st.session_state.get("last_prompt", "") + " " + regen_notes
                    ),
                )

                # --- update preview ---
                st.session_state["html"] = safe

                st.success("Regenerated successfully")

            except Exception as e:
                st.error(e)
