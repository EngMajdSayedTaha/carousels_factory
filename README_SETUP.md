# 🚀 SETUP — @majdst_codes Viral Carousel Factory

This turns a Claude Project into a one-prompt carousel studio. You say *"make a carousel about X"*
→ you get back a **ZIP of publish-ready 1080×1350 PNGs + caption + hashtags**, on-brand, every time.

---

## WHAT'S IN THIS BUNDLE
```
PROJECT_INSTRUCTIONS.md          ← paste into the Project's custom instructions
knowledge/
  ├─ 01_brand_system.md          ← upload as Project knowledge
  ├─ 02_carousel_formats.md      ← upload as Project knowledge
  ├─ 03_hook_bank.md             ← upload as Project knowledge
  ├─ 04_viral_checklist.md       ← upload as Project knowledge
  ├─ 05_caption_hashtag_guide.md ← upload as Project knowledge
  ├─ carousel_engine.py          ← the renderer (host on GitHub — see Step 3)
  ├─ sample_ai_workflow.py       ← AI/dev-hack demo (new slide types) — for reference
  └─ sample_carousel.py          ← code before/after demo — for reference
README_SETUP.md                  ← this file
```

**Covers the whole niche, not just code:** AI tools, dev hacks/workflow, code, and tech. Slide types
include `tool` (tool roundups), `prompt` (steal-my-prompts), `terminal` (CLI hacks), `stat` (big
metrics), `compare` (A vs B), `steps`, `code` (before/after), `quote` (hot takes), and more — plus a
signature **segmented progress rail** on every slide and opt-in font effects (gradient headlines,
outlined stats, CRT scanline). The factory picks the format + slide mix dynamically per topic, and
may ask you one quick question (or for a helper upload) when it sharpens the result.

---

## STEP 1 — Create the Project
Claude → **Projects** → **New project**. Name it `@majdst_codes — Carousel Factory`.

## STEP 2 — Add the brain + knowledge
1. Open **Project instructions** (a.k.a. custom instructions) and paste **all of**
   `PROJECT_INSTRUCTIONS.md`.
2. Add the 5 markdown files in `knowledge/` as **Project knowledge** (upload or paste).
   These give Claude your brand, formats, hooks, checklist, and caption rules.

## STEP 3 — Make the renderer reachable (pick ONE)
The renderer (`carousel_engine.py`) has to run in Claude's code sandbox each chat. **Project
knowledge files are NOT auto-copied into the sandbox** — so give Claude a way to load the engine:

**Option A — Host on GitHub (recommended, cleanest for you as a dev):**
1. Put `carousel_engine.py` in a repo (public, or private — but raw needs to be fetchable).
2. Copy its **raw** URL, e.g. `https://raw.githubusercontent.com/<you>/<repo>/main/carousel_engine.py`.
3. In `PROJECT_INSTRUCTIONS.md` find the RENDER WORKFLOW step 1 and set the engine URL there
   (replace `<RAW_ENGINE_URL>`). Now every chat just runs
   `curl -sL <RAW_ENGINE_URL> -o carousel_engine.py`. ✅ GitHub raw is reachable from the sandbox.

**Option B — Upload per chat:** drag `carousel_engine.py` into the chat; it lands at
`/mnt/user-data/uploads/` and Claude copies it into the working dir. (One extra step each time.)

**Option C — Reproduce from knowledge:** the engine is also in Project knowledge, so Claude can
recreate it in the sandbox with no upload. (Works, but Option A is faster + less error-prone.)

> Tip: Option A is the move. Set it once, forget it.

## STEP 4 — Make a carousel
In the project, just say what you want:
- "Make a carousel about Angular's new `@if` / `@for` control flow."
- "Cheat sheet carousel: 5 SQL joins."
- "Before/after carousel on fixing an `*ngFor` performance bug."
- "Story carousel about a `NULL` that took down a dashboard."

Claude will: pick the best **format**, write the **hook + copy**, run the **viral checklist**,
**render** the slides, and hand you:
- a **ZIP** → `01.png … NN.png` + `caption.txt` (post these in order),
- a **contact sheet** preview inline,
- the **caption + hashtags** to paste.

Tweaks are cheap: "punchier hook", "swap slide 4", "make it 6 slides" → Claude edits + re-renders.

---

## POSTING (manual, your workflow)
1. Download + unzip.
2. New IG carousel post → add `01.png … NN.png` **in order**.
3. Paste the caption from `caption.txt` (or from chat).
4. Post. (Carousels favor **saves + shares** — the recap slide + CTA are built to earn those.)

---

## HOW IT'S BUILT (so you can hack it)
- **Renderer:** Python — Playwright (headless Chromium) renders branded HTML/CSS at 2× then
  Pillow downsamples to exact `1080×1350` (crisp). Pygments does syntax highlighting.
- **Fonts:** Space Grotesk + JetBrains Mono auto-fetched from the google/fonts GitHub mirror
  (Google Fonts CDN is blocked in-sandbox; the mirror is reachable). Base64-embedded into the CSS.
- **Input:** one `carousel.json` (schema in `PROJECT_INSTRUCTIONS.md`). Slide types:
  `hook | text | statement | code | list | recap | cta`.
- **Run it yourself locally:**
  ```bash
  pip install playwright pygments pillow
  playwright install chromium
  python3 sample_ai_workflow.py      # AI/dev-hack demo → ./out_ai  (shows the new slide types)
  python3 sample_carousel.py         # code before/after demo → ./out
  ```
- **Change the canvas to 1:1:** set `W, H = 1080, 1080` near the top of `carousel_engine.py`.

---

## HONEST EXPECTATIONS
No one can *guarantee* virality — that depends on topic, timing, and luck. What this system does
reliably: maximize the **stop-scroll** odds (hook + design) and the **save/share** odds (one idea
per slide, a save-worthy recap, a clean CTA), with a consistent premium look that builds the brand.
Ship consistently (your 2/week cadence), keep sourcing from real work, and the numbers compound.
