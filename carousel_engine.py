#!/usr/bin/env python3
"""
majdst_codes :: CAROUSEL ENGINE
================================
Turns a structured Python/JSON carousel spec into publish-ready Instagram PNGs
(1080x1350, supersampled) + caption.txt, zipped.

Brand: dark / terminal aesthetic, single accent #F9E400, anti-hype.
Signature: a recurring terminal window + prompt/cursor + line-numbered code.

USAGE (in any chat sandbox):
    from carousel_engine import render_carousel
    render_carousel(CAROUSEL, out_dir="out")        # -> out/<slug>.zip

Requires (install once per sandbox):
    pip install playwright pygments pillow --break-system-packages
    playwright install chromium
Fonts: ./fonts/SpaceGrotesk.ttf  +  ./fonts/JetBrainsMono.ttf
   (fetch from github.com/google/fonts if missing — see fetch_fonts())

SLIDE TYPES: hook | text | statement | quote | code | terminal | prompt
             | list | steps | compare | tool | stat | recap | cta
See the docstrings on each render_* function for the accepted fields.
Inline markup inside any text field:
    ==word==     -> accent (#F9E400) highlight
    `word`       -> inline code chip (mono, subtle bg)
"""

import os, re, html, base64, json, zipfile, math, urllib.request

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
W, H = 1080, 1350          # 4:5 portrait = max feed real-estate. Square? set 1080,1080
SCALE = 2                  # render at 2x then downscale -> crisp supersampling
PAD_X, PAD_TOP, PAD_BOT = 92, 84, 80
CONTENT_W = W - 2 * PAD_X  # ~896

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
DISPLAY_TTF = os.path.join(FONT_DIR, "SpaceGrotesk.ttf")
MONO_TTF    = os.path.join(FONT_DIR, "JetBrainsMono.ttf")

FONT_URLS = {  # google/fonts mirror (raw.githubusercontent.com is reachable)
    DISPLAY_TTF: "https://raw.githubusercontent.com/google/fonts/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    MONO_TTF:    "https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}

def fetch_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for path, url in FONT_URLS.items():
        if not os.path.exists(path) or os.path.getsize(path) < 10000:
            urllib.request.urlretrieve(url, path)

def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ----------------------------------------------------------------------------
# CSS  (tokens live in :root so no Python interpolation is needed in the CSS)
# ----------------------------------------------------------------------------
def fonts_css():
    fetch_fonts()
    disp = _b64(DISPLAY_TTF)
    mono = _b64(MONO_TTF)
    block = """
@font-face{font-family:'Disp';src:url(data:font/ttf;base64,__DISP__) format('truetype');font-weight:100 800;font-display:block;}
@font-face{font-family:'Mono';src:url(data:font/ttf;base64,__MONO__) format('truetype');font-weight:100 800;font-display:block;}
"""
    return block.replace("__DISP__", disp).replace("__MONO__", mono)

BASE_CSS = """
:root{
  --bg:#0A0A0C; --bg-soft:#101014; --bg-bar:#17171C;
  --line:#26262E; --line-soft:#1A1A20;
  --ink:#ECECEE; --dim:#9A9AA4; --faint:#56565F;
  --accent:#F9E400; --accent-soft:rgba(249,228,0,0.12);
  --red:#FF6B5E; --amber:#FFB454; --green:#5BE08A; --blue:#82AAFF;
  --disp:'Disp','Space Grotesk',system-ui,sans-serif;
  --mono:'Mono','JetBrains Mono',ui-monospace,monospace;
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision;}
html,body{width:1080px;height:1350px;}
.slide{
  position:relative;width:1080px;height:1350px;overflow:hidden;
  background-color:var(--bg);
  background-image:radial-gradient(rgba(255,255,255,0.022) 1px, transparent 1px);
  background-size:34px 34px;background-position:center;
  color:var(--ink);font-family:var(--disp);
  display:flex;flex-direction:column;
  padding:84px 92px 80px 92px;
}
/* depth: soft vignette + faint top accent glow */
.slide::before{content:"";position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(120% 80% at 50% 0%, rgba(249,228,0,0.05), transparent 42%),
             radial-gradient(140% 100% at 50% 100%, rgba(0,0,0,0.55), transparent 60%);}
.slide.hero::before{background:radial-gradient(120% 70% at 50% -8%, rgba(249,228,0,0.10), transparent 46%),
             radial-gradient(140% 100% at 50% 100%, rgba(0,0,0,0.6), transparent 55%);}

/* ---- header / footer chrome ---- */
.head{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;
  font-family:var(--mono);font-size:21px;letter-spacing:.02em;}
.head .brand{color:var(--dim);}
.head .brand b{color:var(--ink);font-weight:600;}
.head .count{color:var(--faint);font-weight:500;}
.foot{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;
  font-family:var(--mono);font-size:20px;}
.foot .h{color:var(--faint);}
.foot .swipe{color:var(--dim);font-weight:500;}
.foot .swipe i{color:var(--accent);font-style:normal;margin-left:6px;
  text-shadow:0 0 16px rgba(249,228,0,.45);}
.foot.center{justify-content:center;}

/* ---- body container ---- */
.body{position:relative;z-index:2;flex:1;display:flex;flex-direction:column;min-height:0;}
.body.mid{justify-content:center;}
.body.top{justify-content:flex-start;padding-top:18px;}

/* ---- prompt + cursor signature ---- */
.prompt{font-family:var(--mono);font-size:24px;color:var(--faint);margin-bottom:30px;letter-spacing:.01em;}
.prompt .u{color:var(--accent);} .prompt .h{color:var(--dim);} .prompt .p{color:var(--faint);}
.prompt .cmd{color:var(--dim);}
.cursor{display:inline-block;width:13px;height:26px;background:var(--accent);
  margin-left:6px;vertical-align:-4px;box-shadow:0 0 18px rgba(249,228,0,.55);border-radius:1px;}

/* ---- kicker / eyebrow ---- */
.kicker{font-family:var(--mono);font-weight:700;font-size:22px;letter-spacing:.24em;
  text-transform:uppercase;color:var(--accent);margin-bottom:28px;
  text-shadow:0 0 22px rgba(249,228,0,.35);}

/* ---- headlines ---- */
.hook{font-family:var(--disp);font-weight:700;line-height:1.02;letter-spacing:-.025em;color:var(--ink);}
.h-title{font-family:var(--disp);font-weight:600;font-size:58px;line-height:1.06;letter-spacing:-.02em;}
.statement{font-family:var(--disp);font-weight:600;font-size:66px;line-height:1.08;letter-spacing:-.022em;}
.body-text{font-family:var(--disp);font-weight:400;font-size:33px;line-height:1.42;color:var(--dim);margin-top:30px;max-width:880px;}

/* inline markup */
.ac{color:var(--accent);font-weight:600;}
.hook .ac{text-shadow:0 0 30px rgba(249,228,0,.40);}
.chip{font-family:var(--mono);font-size:.86em;background:var(--bg-soft);border:1px solid var(--line);
  border-radius:7px;padding:.06em .34em;color:#FFE873;}
/* code token inside a DISPLAY heading: mono + accent, no box (keeps I vs l legible) */
.kmono{font-family:var(--mono);font-weight:600;font-size:.82em;letter-spacing:-.01em;color:var(--accent);
  text-shadow:0 0 26px rgba(249,228,0,.34);}

/* ---- list ---- */
.list{margin-top:38px;display:flex;flex-direction:column;gap:26px;}
.li{display:flex;align-items:flex-start;gap:24px;}
.li .ix{font-family:var(--mono);font-weight:700;font-size:25px;color:var(--accent);
  min-width:46px;padding-top:7px;text-shadow:0 0 16px rgba(249,228,0,.3);}
.li .lt{font-family:var(--disp);font-weight:500;font-size:35px;line-height:1.28;color:var(--ink);}
.li .lt small{display:block;font-weight:400;font-size:26px;color:var(--dim);margin-top:6px;line-height:1.32;}
.divider{height:1px;background:var(--line-soft);margin:30px 0;}

/* ---- terminal window (code) ---- */
.win{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:var(--bg-soft);
  box-shadow:0 30px 80px rgba(0,0,0,.5);margin-top:34px;}
.winbar{display:flex;align-items:center;gap:11px;padding:18px 22px;background:var(--bg-bar);
  border-bottom:1px solid var(--line);}
.dot{width:14px;height:14px;border-radius:50%;}
.dot.r{background:var(--red);} .dot.a{background:var(--amber);} .dot.g{background:var(--green);}
.winname{font-family:var(--mono);font-size:22px;color:var(--dim);margin-left:14px;}
.winbadge{margin-left:auto;font-family:var(--mono);font-weight:700;font-size:18px;letter-spacing:.16em;
  padding:5px 12px;border-radius:7px;text-transform:uppercase;}
.winbadge.before{color:var(--red);border:1px solid rgba(255,107,94,.4);background:rgba(255,107,94,.08);}
.winbadge.after{color:var(--accent);border:1px solid rgba(249,228,0,.45);background:var(--accent-soft);
  text-shadow:0 0 18px rgba(249,228,0,.4);}
.winbody{padding:30px 26px 32px 26px;}

/* pygments code (table line numbers). font-size injected inline per slide. */
.cb,.cb pre{font-family:var(--mono);line-height:1.62;margin:0;white-space:pre;}
table.cbtable{border-collapse:collapse;width:100%;}
table.cbtable td{vertical-align:top;padding:0;border:none;}
td.linenos{user-select:none;text-align:right;padding-right:24px;}
.linenodiv pre{color:var(--faint);opacity:.65;}
td.code{width:100%;}
.cb .c,.cb .c1,.cb .cm,.cb .cp,.cb .cs{color:#5C5C66;font-style:italic;}
.cb .k,.cb .kd,.cb .kn,.cb .kc,.cb .kr,.cb .kt{color:#C792EA;}
.cb .s,.cb .s1,.cb .s2,.cb .sb,.cb .se,.cb .dl,.cb .sd{color:#C3E88D;}
.cb .nf,.cb .fm{color:#82AAFF;}
.cb .mi,.cb .mf,.cb .mh,.cb .mo,.cb .il{color:#F78C6C;}
.cb .o,.cb .ow{color:#89DDFF;}
.cb .p{color:#9AA0AB;}
.cb .n,.cb .nx,.cb .nv,.cb .vi{color:#E6E6E8;}
.cb .nb,.cb .bp,.cb .nc,.cb .nn{color:#FFCB6B;}
.cb .nt{color:#82AAFF;} .cb .na{color:#C792EA;} .cb .nd{color:#82AAFF;}
.cb .kc{color:#FF9D6B;}
/* a subtle '+' / '-' diff option */
.diffline{display:block;}
.diffline.add{background:rgba(91,224,138,.10);box-shadow:inset 4px 0 var(--green);}
.diffline.del{background:rgba(255,107,94,.10);box-shadow:inset 4px 0 var(--red);}

/* ---- cta card ---- */
.cta-card{border:1px solid var(--line);border-radius:18px;background:linear-gradient(180deg,var(--bg-soft),#0c0c10);
  padding:54px 50px;box-shadow:0 30px 90px rgba(0,0,0,.5);}
.cta-card .big{font-family:var(--disp);font-weight:700;font-size:60px;line-height:1.04;letter-spacing:-.022em;}
.cta-card .sub{font-family:var(--disp);font-weight:400;font-size:31px;color:var(--dim);margin-top:24px;line-height:1.4;}
.cta-row{display:flex;align-items:center;gap:16px;margin-top:46px;flex-wrap:wrap;}
.pill{font-family:var(--mono);font-weight:600;font-size:25px;padding:14px 24px;border-radius:11px;
  border:1px solid var(--line);color:var(--ink);background:var(--bg);}
.pill.accent{background:var(--accent);color:#0A0A0C;border-color:var(--accent);
  box-shadow:0 0 36px rgba(249,228,0,.32);}
.pill .mut{color:var(--dim);}

/* ========================================================================
   SIGNATURE PROGRESS RAIL  (segmented terminal/loading bar in the footer)
   ======================================================================== */
.foot-wrap{position:relative;z-index:2;display:flex;flex-direction:column;gap:22px;}
.prog{display:flex;gap:8px;align-items:center;height:7px;}
.prog .seg{flex:1;height:3px;border-radius:3px;background:var(--line);}
.prog .seg.done{background:rgba(249,228,0,.42);}
.prog .seg.cur{height:7px;background:var(--accent);box-shadow:0 0 16px rgba(249,228,0,.7);}

/* ========================================================================
   FONT EFFECTS  (opt-in, used sparingly)
   ======================================================================== */
.gradtext{background:linear-gradient(118deg,var(--accent) 0%,#FFF6B0 46%,var(--ink) 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;}
/* subtle CRT scanline on hero slides */
.slide.hero::after{content:"";position:absolute;inset:0;pointer-events:none;opacity:.55;z-index:1;
  background:repeating-linear-gradient(to bottom,rgba(255,255,255,.014) 0 1px,transparent 1px 4px);}

/* ========================================================================
   COMPARE  (two-column A vs B — no code needed)
   ======================================================================== */
.cmp{display:flex;gap:24px;margin-top:42px;}
.cmp .col{flex:1;border:1px solid var(--line);border-radius:16px;background:var(--bg-soft);
  padding:32px 28px;display:flex;flex-direction:column;}
.cmp .col.win{border-color:rgba(249,228,0,.5);box-shadow:0 0 44px rgba(249,228,0,.12);
  background:linear-gradient(180deg,rgba(249,228,0,.05),var(--bg-soft));}
.cmp .clabel{font-family:var(--mono);font-weight:700;font-size:22px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--dim);margin-bottom:24px;}
.cmp .col.win .clabel{color:var(--accent);text-shadow:0 0 18px rgba(249,228,0,.4);}
.cmp .citem{font-family:var(--disp);font-size:28px;line-height:1.32;color:var(--ink);
  padding:14px 0;border-top:1px solid var(--line-soft);display:flex;gap:14px;align-items:flex-start;}
.cmp .citem:first-of-type{border-top:none;padding-top:0;}
.cmp .citem .mk{font-family:var(--mono);font-size:24px;flex-shrink:0;line-height:1.4;}
.cmp .col .mk{color:var(--red);} .cmp .col.win .mk{color:var(--green);}
.cmp .col.neutral .mk{color:var(--dim);} .cmp .col.win.neutral .mk{color:var(--accent);}

/* ========================================================================
   STEPS  (numbered process with connector spine)
   ======================================================================== */
.steps{margin-top:40px;display:flex;flex-direction:column;}
.step{display:flex;gap:26px;padding:16px 0;position:relative;}
.step::before{content:"";position:absolute;left:27px;top:62px;bottom:-4px;width:1px;background:var(--line);}
.step:last-child::before{display:none;}
.step .sn{font-family:var(--mono);font-weight:700;font-size:25px;color:var(--accent);
  min-width:54px;height:54px;border:1px solid rgba(249,228,0,.35);border-radius:13px;
  display:flex;align-items:center;justify-content:center;background:var(--accent-soft);
  text-shadow:0 0 14px rgba(249,228,0,.3);flex-shrink:0;z-index:1;}
.step .stxt{padding-top:5px;}
.step .st{font-family:var(--disp);font-weight:600;font-size:34px;line-height:1.22;color:var(--ink);}
.step .ss{font-family:var(--disp);font-weight:400;font-size:26px;color:var(--dim);
  margin-top:7px;line-height:1.36;}

/* ========================================================================
   PROMPT  (AI prompt showcase — the killer slide for AI content)
   ======================================================================== */
.pbox{margin-top:38px;border:1px solid var(--line);border-radius:16px;overflow:hidden;
  background:var(--bg-soft);box-shadow:0 30px 80px rgba(0,0,0,.5);}
.pbar{display:flex;align-items:center;gap:12px;padding:18px 24px;background:var(--bg-bar);
  border-bottom:1px solid var(--line);}
.pbar .ptag{font-family:var(--mono);font-weight:700;font-size:19px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--accent);text-shadow:0 0 16px rgba(249,228,0,.35);}
.pbar .pname{font-family:var(--mono);font-size:21px;color:var(--dim);margin-left:auto;}
.ptext{padding:32px 28px;font-family:var(--mono);font-size:27px;line-height:1.58;
  color:var(--ink);white-space:pre-wrap;}
.ptext .vr{color:var(--accent);}

/* ========================================================================
   STAT  (one giant metric)
   ======================================================================== */
.stat{display:flex;flex-direction:column;align-items:flex-start;}
.stat .sv{font-family:var(--disp);font-weight:700;font-size:210px;line-height:.9;
  letter-spacing:-.045em;color:var(--accent);text-shadow:0 0 60px rgba(249,228,0,.35);}
.stat .sv.outline{color:transparent;-webkit-text-stroke:3px var(--accent);text-shadow:none;}
.stat .sl{font-family:var(--disp);font-weight:600;font-size:50px;line-height:1.1;
  color:var(--ink);margin-top:14px;max-width:860px;letter-spacing:-.015em;}
.stat .ssub{font-family:var(--disp);font-weight:400;font-size:30px;color:var(--dim);
  margin-top:22px;max-width:820px;line-height:1.4;}

/* ========================================================================
   TOOL  (featured tool card — for AI-tool roundups)
   ======================================================================== */
.tool{margin-top:30px;border:1px solid var(--line);border-radius:18px;
  background:linear-gradient(180deg,var(--bg-soft),#0c0c10);padding:42px 38px;
  box-shadow:0 30px 80px rgba(0,0,0,.5);}
.tool .thead{display:flex;align-items:center;gap:18px;}
.tool .tnum{font-family:var(--mono);font-weight:700;font-size:24px;color:#0A0A0C;
  background:var(--accent);border-radius:10px;padding:8px 15px;box-shadow:0 0 28px rgba(249,228,0,.4);}
.tool .tname{font-family:var(--disp);font-weight:700;font-size:54px;letter-spacing:-.02em;color:var(--ink);}
.tool .ttag{font-family:var(--mono);font-size:24px;color:var(--dim);margin-top:8px;}
.tool .tpts{margin-top:28px;display:flex;flex-direction:column;gap:18px;}
.tool .tpt{font-family:var(--disp);font-size:30px;line-height:1.32;color:var(--ink);
  display:flex;gap:14px;align-items:flex-start;}
.tool .tpt .b{color:var(--accent);font-family:var(--mono);flex-shrink:0;}
.tool .turl{font-family:var(--mono);font-size:22px;color:var(--accent);margin-top:28px;
  text-shadow:0 0 16px rgba(249,228,0,.3);}

/* ========================================================================
   TERMINAL  (command + output session — CLI hacks)
   ======================================================================== */
.term{margin-top:32px;}
.term .winbody{padding:28px 26px 30px 26px;}
.tline{font-family:var(--mono);font-size:25px;line-height:1.62;white-space:pre-wrap;word-break:break-word;}
.tline .tp{color:var(--accent);}
.tline.cmd{color:var(--ink);}
.tline.out{color:var(--dim);}
.tline.cmt{color:var(--faint);font-style:italic;}
.tline.ok{color:var(--green);}

/* ========================================================================
   QUOTE  (pull-quote / hot take — engagement driver)
   ======================================================================== */
.quote{position:relative;margin-top:18px;}
.quote .qm{font-family:var(--disp);font-weight:700;font-size:130px;color:var(--accent);
  opacity:.22;line-height:.55;}
.quote .qt{font-family:var(--disp);font-weight:600;font-size:56px;line-height:1.18;
  letter-spacing:-.02em;color:var(--ink);margin-top:-8px;}
.quote .qa{font-family:var(--mono);font-size:24px;color:var(--dim);margin-top:32px;}
.quote .qa::before{content:"\\2014\\00a0";}
"""

# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def mk(text):
    """escape + apply inline markup for BODY text (==accent==, `chip`)."""
    if text is None:
        return ""
    t = html.escape(str(text))
    t = re.sub(r"==(.+?)==", r'<span class="ac">\1</span>', t)
    t = re.sub(r"`(.+?)`", r'<span class="chip">\1</span>', t)
    t = t.replace("\n", "<br>")
    return t

def mkd(text):
    """escape + inline markup for DISPLAY headings: `code`->mono accent, ==x==->accent."""
    if text is None:
        return ""
    t = html.escape(str(text))
    t = re.sub(r"==(.+?)==", r'<span class="ac">\1</span>', t)
    t = re.sub(r"`(.+?)`", r'<span class="kmono">\1</span>', t)
    t = t.replace("\n", "<br>")
    return t

def hook_size(title):
    """auto-fit hook headline by raw length (markup stripped)."""
    plain = re.sub(r"==|`", "", title or "")
    n = len(plain)
    if n <= 20:  return 108
    if n <= 32:  return 92
    if n <= 48:  return 78
    if n <= 68:  return 66
    if n <= 92:  return 56
    return 48

def highlight_code(code, lang):
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    try:
        lexer = get_lexer_by_name(lang, stripnl=False)
    except Exception:
        try: lexer = guess_lexer(code)
        except Exception: lexer = get_lexer_by_name("text")
    fmt = HtmlFormatter(nowrap=False, linenos="table", cssclass="cb")
    return highlight(code.rstrip("\n"), lexer, fmt)

def code_font_size(code):
    """shrink mono font so the longest line fits CONTENT_W (no h-overflow)."""
    longest = max((len(l) for l in code.splitlines()), default=1)
    # gutter ~ 3-4 chars; mono advance ~0.602em
    avail = CONTENT_W - 96  # window padding + gutter
    size = avail / (max(longest, 1) * 0.602)
    return int(max(17, min(31, size)))

PROMPT = ('<span class="u">majdst</span><span class="p">@</span>'
          '<span class="h">codes</span><span class="p">:~$</span> ')

# ----------------------------------------------------------------------------
# slide renderers  ->  (body_inner_html, body_align, hero_flag)
# ----------------------------------------------------------------------------
def render_hook(s):
    """hook: {kicker?, title, cmd?(prompt text), sub?}"""
    fs = s.get("size") or hook_size(s.get("title", ""))
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    prompt = (f'<div class="prompt">{PROMPT}<span class="cmd">{mk(s.get("cmd",""))}</span>'
              f'<span class="cursor"></span></div>')
    sub = f'<div class="body-text" style="margin-top:34px;">{mk(s["sub"])}</div>' if s.get("sub") else ""
    hcls = "hook gradtext" if s.get("grad") else "hook"
    inner = (f'{prompt}{kicker}'
             f'<div class="{hcls}" style="font-size:{fs}px;">{mkd(s["title"])}</div>{sub}')
    return inner, "mid", True

def render_text(s):
    """text/statement: {kicker?, title, body?}  (use type 'statement' for big centered)"""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    cls = "statement" if s.get("type") == "statement" else "h-title"
    if s.get("grad"): cls += " gradtext"
    body = f'<div class="body-text">{mk(s["body"])}</div>' if s.get("body") else ""
    align = "mid" if s.get("type") == "statement" else "top"
    inner = f'{kicker}<div class="{cls}">{mkd(s["title"])}</div>{body}'
    return inner, align, False

def render_recap(s):
    """recap: {kicker?, title, body?} centered, punchy summary"""
    kicker = f'<div class="kicker">{mk(s.get("kicker","recap"))}</div>'
    body = f'<div class="body-text" style="font-size:36px;color:var(--ink);">{mk(s["body"])}</div>' if s.get("body") else ""
    inner = f'{kicker}<div class="statement">{mkd(s["title"])}</div>{body}'
    return inner, "mid", False

def render_list(s):
    """list: {kicker?, title, items:[str | {t, sub?}]}"""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    title = f'<div class="h-title">{mkd(s["title"])}</div>' if s.get("title") else ""
    rows = []
    for i, it in enumerate(s["items"], 1):
        if isinstance(it, dict):
            sub = f'<small>{mk(it.get("sub",""))}</small>' if it.get("sub") else ""
            lt = f'{mkd(it["t"])}{sub}'
        else:
            lt = mkd(it)
        rows.append(f'<div class="li"><div class="ix">{i:02d}</div><div class="lt">{lt}</div></div>')
    inner = f'{kicker}{title}<div class="list">{"".join(rows)}</div>'
    return inner, "top", False

def render_code(s):
    """code: {kicker?, title?, filename, lang, code, label? ('BEFORE'|'AFTER'), note?}"""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    title = f'<div class="h-title" style="font-size:46px;">{mkd(s["title"])}</div>' if s.get("title") else ""
    badge = ""
    if s.get("label"):
        cls = "after" if s["label"].upper() == "AFTER" else "before"
        badge = f'<span class="winbadge {cls}">{html.escape(s["label"])}</span>'
    fs = code_font_size(s["code"])
    code_html = highlight_code(s["code"], s.get("lang", "text"))
    note = f'<div class="body-text" style="font-size:28px;margin-top:24px;">{mk(s["note"])}</div>' if s.get("note") else ""
    win = (f'<div class="win"><div class="winbar">'
           f'<span class="dot r"></span><span class="dot a"></span><span class="dot g"></span>'
           f'<span class="winname">{html.escape(s.get("filename","snippet"))}</span>{badge}</div>'
           f'<div class="winbody" style="font-size:{fs}px;">{code_html}</div></div>')
    inner = f'{kicker}{title}{win}{note}'
    return inner, "top", False

def render_cta(s):
    """cta: {title, body?, primary?, secondary?, site?}"""
    primary = s.get("primary", "Follow @majdst_codes")
    secondary = s.get("secondary", "Save this for later")
    site = s.get("site", "majdst.codes")
    prompt = f'<div class="prompt" style="margin-bottom:34px;">{PROMPT}<span class="cmd">{mk(s.get("cmd","follow --for-real-dev-content"))}</span><span class="cursor"></span></div>'
    body = f'<div class="sub">{mk(s["body"])}</div>' if s.get("body") else ""
    card = (f'<div class="cta-card">{prompt}'
            f'<div class="big">{mkd(s["title"])}</div>{body}'
            f'<div class="cta-row">'
            f'<span class="pill accent">{html.escape(secondary)}</span>'
            f'<span class="pill">{html.escape(primary)}</span></div>'
            f'<div class="cta-row" style="margin-top:22px;">'
            f'<span class="pill"><span class="mut">$</span> open {html.escape(site)}</span></div>'
            f'</div>')
    return card, "mid", True

# ----------------------------------------------------------------------------
# extended slide renderers (broader niche: AI tools / dev hacks / tech)
# ----------------------------------------------------------------------------
def _kt(s, title_size=None):
    """shared kicker + optional title block."""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    if s.get("title"):
        st = f' style="font-size:{title_size}px;"' if title_size else ""
        title = f'<div class="h-title"{st}>{mkd(s["title"])}</div>'
    else:
        title = ""
    return kicker, title

def render_compare(s):
    """compare: {kicker?, title?, left:{label,items}, right:{label,items}, winner?('left'|'right'), neutral?}"""
    kicker, title = _kt(s, title_size=48)
    winner = s.get("winner", "right")
    neutral = s.get("neutral", False)
    def col(side, data):
        is_win = (side == winner)
        cls = "col" + (" win" if is_win else "") + (" neutral" if neutral else "")
        label = f'<div class="clabel">{mk(data.get("label",""))}</div>'
        if neutral:
            mark = "&#9656;"
        else:
            mark = "&#10003;" if is_win else "&#10007;"
        items = "".join(
            f'<div class="citem"><span class="mk">{mark}</span><span>{mkd(it)}</span></div>'
            for it in data.get("items", [])
        )
        return f'<div class="{cls}">{label}{items}</div>'
    body = f'<div class="cmp">{col("left", s["left"])}{col("right", s["right"])}</div>'
    return f'{kicker}{title}{body}', "top", False

def render_steps(s):
    """steps: {kicker?, title?, steps:[str | {t, sub?}]}"""
    kicker, title = _kt(s)
    rows = []
    for i, it in enumerate(s["steps"], 1):
        if isinstance(it, dict):
            sub = f'<div class="ss">{mk(it.get("sub",""))}</div>' if it.get("sub") else ""
            t = f'<div class="st">{mkd(it["t"])}</div>'
        else:
            sub, t = "", f'<div class="st">{mkd(it)}</div>'
        rows.append(f'<div class="step"><div class="sn">{i:02d}</div><div class="stxt">{t}{sub}</div></div>')
    return f'{kicker}{title}<div class="steps">{"".join(rows)}</div>', "top", False

def render_prompt(s):
    """prompt: {kicker?, title?, prompt, label?, tool?, note?}  — {vars} render in accent"""
    kicker, title = _kt(s)
    ptext = html.escape(s["prompt"])
    ptext = re.sub(r"\{([^}]+)\}", r'<span class="vr">{\1}</span>', ptext)
    tag = html.escape(s.get("label", "PROMPT"))
    name = f'<span class="pname">{html.escape(s["tool"])}</span>' if s.get("tool") else ""
    note = f'<div class="body-text" style="font-size:28px;margin-top:24px;">{mk(s["note"])}</div>' if s.get("note") else ""
    box = (f'<div class="pbox"><div class="pbar"><span class="ptag">{tag}</span>{name}</div>'
           f'<div class="ptext">{ptext}</div></div>')
    return f'{kicker}{title}{box}{note}', "top", False

def render_stat(s):
    """stat: {kicker?, value, label, sub?, outline?, grad?}"""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    vcls = "sv"
    if s.get("outline"): vcls += " outline"
    if s.get("grad"):    vcls += " gradtext"
    sub = f'<div class="ssub">{mk(s["sub"])}</div>' if s.get("sub") else ""
    inner = (f'{kicker}<div class="stat"><div class="{vcls}">{mkd(s["value"])}</div>'
             f'<div class="sl">{mkd(s["label"])}</div>{sub}</div>')
    return inner, "mid", True

def render_tool(s):
    """tool: {kicker?, title?, num?, name, tagline?, points:[...], url?}"""
    kicker, title = _kt(s)
    num = f'<span class="tnum">{html.escape(str(s["num"]))}</span>' if s.get("num") else ""
    tag = f'<div class="ttag">{mk(s["tagline"])}</div>' if s.get("tagline") else ""
    pts = "".join(
        f'<div class="tpt"><span class="b">&#9656;</span><span>{mkd(p)}</span></div>'
        for p in s.get("points", [])
    )
    url = f'<div class="turl">&#8599; {html.escape(s["url"])}</div>' if s.get("url") else ""
    card = (f'<div class="tool"><div class="thead">{num}<div>'
            f'<div class="tname">{mkd(s["name"])}</div>{tag}</div></div>'
            f'<div class="tpts">{pts}</div>{url}</div>')
    return f'{kicker}{title}{card}', "top", False

def render_terminal(s):
    """terminal: {kicker?, title?, name?, lines:[{cmd}|{out}|{ok}|{comment}]}"""
    kicker, title = _kt(s)
    name = html.escape(s.get("name", "bash"))
    rows = []
    for ln in s["lines"]:
        if "cmd" in ln:
            rows.append(f'<div class="tline cmd"><span class="tp">$</span> {html.escape(ln["cmd"])}</div>')
        elif "ok" in ln:
            rows.append(f'<div class="tline ok">{html.escape(ln["ok"])}</div>')
        elif "out" in ln:
            rows.append(f'<div class="tline out">{html.escape(ln["out"])}</div>')
        elif "comment" in ln:
            rows.append(f'<div class="tline cmt"># {html.escape(ln["comment"])}</div>')
    win = (f'<div class="win term"><div class="winbar">'
           f'<span class="dot r"></span><span class="dot a"></span><span class="dot g"></span>'
           f'<span class="winname">{name}</span></div>'
           f'<div class="winbody">{"".join(rows)}</div></div>')
    return f'{kicker}{title}{win}', "top", False

def render_quote(s):
    """quote: {kicker?, quote, attribution?}"""
    kicker = f'<div class="kicker">{mk(s["kicker"])}</div>' if s.get("kicker") else ""
    attr = f'<div class="qa">{mk(s["attribution"])}</div>' if s.get("attribution") else ""
    inner = (f'{kicker}<div class="quote"><div class="qm">&ldquo;</div>'
             f'<div class="qt">{mkd(s["quote"])}</div>{attr}</div>')
    return inner, "mid", False


RENDERERS = {
    "hook": render_hook, "text": render_text, "statement": render_text,
    "recap": render_recap, "list": render_list, "code": render_code, "cta": render_cta,
    "compare": render_compare, "steps": render_steps, "prompt": render_prompt,
    "stat": render_stat, "tool": render_tool, "terminal": render_terminal, "quote": render_quote,
}

# ----------------------------------------------------------------------------
# frame + full document
# ----------------------------------------------------------------------------
def build_slide_html(slide, idx, total, cfg):
    fn = RENDERERS.get(slide["type"])
    if not fn:
        raise ValueError(f"unknown slide type: {slide['type']}")
    inner, align, hero = fn(slide)
    handle = cfg.get("handle", "@majdst_codes")
    brand = f'<span class="brand">~/<b>{html.escape(handle.lstrip("@"))}</b></span>'
    count = f'<span class="count">[{idx:02d}/{total:02d}]</span>'
    last = idx == total
    # signature segmented progress rail
    if last:
        rail_segs = "".join('<span class="seg done"></span>' for _ in range(total))
        meta = ('<div class="foot center"><span class="h">'
                + html.escape(cfg.get("site", "majdst.codes")) + '</span></div>')
    else:
        cells = []
        for k in range(1, total + 1):
            c = "seg done" if k < idx else ("seg cur" if k == idx else "seg")
            cells.append(f'<span class="{c}"></span>')
        rail_segs = "".join(cells)
        meta = (f'<div class="foot"><span class="h">{html.escape(handle)}</span>'
                f'<span class="swipe">swipe<i>&rarr;</i></span></div>')
    foot = f'<div class="foot-wrap">{meta}<div class="prog">{rail_segs}</div></div>'
    slide_cls = "slide hero" if hero else "slide"
    body = f'<div class="body {align}">{inner}</div>'
    return (f'<div class="{slide_cls}">'
            f'<div class="head">{brand}{count}</div>'
            f'{body}{foot}</div>')

def full_doc(slide_html):
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{fonts_css()}{BASE_CSS}</style></head>"
            f"<body>{slide_html}</body></html>")

# ----------------------------------------------------------------------------
# render + zip
# ----------------------------------------------------------------------------
def slugify(t):
    return re.sub(r"[^a-z0-9]+", "_", (t or "carousel").lower()).strip("_")[:42] or "carousel"

def render_carousel(carousel, out_dir="out", keep_html=False):
    from playwright.sync_api import sync_playwright
    from PIL import Image
    cfg = {k: carousel[k] for k in ("handle", "site") if k in carousel}
    slides = carousel["slides"]
    total = len(slides)
    os.makedirs(out_dir, exist_ok=True)
    png_dir = os.path.join(out_dir, "_png"); os.makedirs(png_dir, exist_ok=True)

    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb", "--disable-lcd-text"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
        for i, slide in enumerate(slides, 1):
            doc = full_doc(build_slide_html(slide, i, total, cfg))
            page.set_content(doc, wait_until="load")
            page.evaluate("async () => { await document.fonts.ready; }")
            raw = os.path.join(png_dir, f"_raw_{i:02d}.png")
            page.locator(".slide").screenshot(path=raw)
            # supersample down to exact IG spec
            img = Image.open(raw).convert("RGB").resize((W, H), Image.LANCZOS)
            final = os.path.join(png_dir, f"{i:02d}.png")
            img.save(final, "PNG", optimize=True)
            os.remove(raw)
            paths.append(final)
            if keep_html:
                with open(os.path.join(out_dir, f"slide_{i:02d}.html"), "w") as f:
                    f.write(doc)
        browser.close()

    # caption file
    cap = build_caption_text(carousel)
    cap_path = os.path.join(out_dir, "caption.txt")
    with open(cap_path, "w") as f:
        f.write(cap)

    # zip
    slug = slugify(carousel.get("slug") or carousel.get("title") or (slides[0].get("title")))
    zip_path = os.path.join(out_dir, f"majdst_{slug}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths:
            z.write(pth, os.path.basename(pth))
        z.write(cap_path, "caption.txt")

    # preview contact sheet (always, so it can be shown in chat)
    sheet_path = os.path.join(out_dir, "contact_sheet.png")
    try:
        _contact_sheet(paths, sheet_path)
    except Exception:
        sheet_path = None
    return {"zip": zip_path, "pngs": paths, "caption": cap_path,
            "contact_sheet": sheet_path, "count": total}

def _contact_sheet(paths, out_path, cols=4, tw=430):
    from PIL import Image
    ims = [Image.open(p) for p in paths]
    rows = math.ceil(len(ims) / cols)
    th = int(tw * ims[0].height / ims[0].width)
    pad, bg = 14, (18, 18, 22)
    sheet = Image.new("RGB", (cols*tw+(cols+1)*pad, rows*th+(rows+1)*pad), bg)
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), (pad+c*(tw+pad), pad+r*(th+pad)))
    sheet.save(out_path)

def build_caption_text(carousel):
    title = carousel.get("title", "")
    hook = carousel.get("caption_hook") or (carousel["slides"][0].get("title", ""))
    body = carousel.get("caption_body", "")
    cta = carousel.get("caption_cta", "Save this for your next refactor & follow @majdst_codes for real-world dev content.\n\nDeep dives + the community → majdst.codes")
    tags = carousel.get("hashtags", [])
    plain_hook = re.sub(r"==|`", "", hook)
    parts = [plain_hook.strip()]
    if body: parts.append(body.strip())
    parts.append(cta.strip())
    if tags:
        parts.append(" ".join(t if t.startswith("#") else f"#{t}" for t in tags))
    return "\n\n".join(parts) + "\n"


if __name__ == "__main__":
    # render a carousel.json next to this file if present
    here = os.path.dirname(os.path.abspath(__file__))
    jpath = os.path.join(here, "carousel.json")
    if os.path.exists(jpath):
        with open(jpath) as f:
            data = json.load(f)
        out = render_carousel(data, out_dir=os.path.join(here, "out"), keep_html=False)
        print(json.dumps(out, indent=2))
    else:
        print("no carousel.json found — import render_carousel(...) instead.")
