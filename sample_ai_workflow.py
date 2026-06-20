#!/usr/bin/env python3
"""Sample carousel — broader niche (AI tools / dev hacks). Exercises the new
slide types + the signature progress rail. Run: python3 sample_ai_workflow.py"""
from carousel_engine import render_carousel

CAROUSEL = {
    "handle": "@majdst_codes",
    "site": "majdst.codes",
    "slug": "ai_dev_setup",
    "title": "The AI dev setup that saves 10 hrs/week",
    "slides": [
        {"type": "hook", "grad": True, "kicker": "AI WORKFLOW", "cmd": "setup --ai",
         "title": "The AI setup that saved me `10 hrs` a week."},

        {"type": "stat", "kicker": "the result", "value": "10h",
         "label": "saved every week on boilerplate + context-switching",
         "sub": "Not magic. Just the right AI wired into the editor."},

        {"type": "tool", "kicker": "tool 01", "num": "01", "name": "Cursor",
         "tagline": "AI-native code editor (a VS Code fork)",
         "points": [
             "`Cmd+K` — edit code inline with a prompt",
             "`Cmd+L` — chat that ==knows your whole repo==",
             "Tab completes multi-line edits, not just words",
         ],
         "url": "cursor.com"},

        {"type": "prompt", "kicker": "steal this", "title": "My go-to refactor prompt",
         "label": "PROMPT", "tool": "Cursor · Cmd+K",
         "prompt": "Refactor this into smaller functions.\nKeep the public API identical.\nAdd types for {inputs} and {return}.\nNo new dependencies.",
         "note": "The ==constraints== matter more than the ask."},

        {"type": "compare", "kicker": "why in-editor", "title": "Where the time actually goes",
         "winner": "right",
         "left": {"label": "Copy-paste ChatGPT",
                  "items": ["Switch window, lose context",
                            "Re-explain your codebase",
                            "Paste back, fix the imports"]},
         "right": {"label": "AI in the editor",
                   "items": ["Stays in your flow",
                             "Already has repo context",
                             "Edits land in the file"]}},

        {"type": "terminal", "kicker": "bonus hack", "title": "Let AI write your commits",
         "name": "bash",
         "lines": [
             {"comment": "stage your changes, then:"},
             {"cmd": "aider --commit"},
             {"out": "analyzing diff..."},
             {"ok": "feat: add retry logic to the fetch client"},
         ]},

        {"type": "steps", "kicker": "get started", "title": "Wire it up in 3 steps",
         "steps": [
             {"t": "Install `Cursor`",
              "sub": "Import your VS Code settings + extensions in one click"},
             {"t": "Add a model key (or use the built-ins)",
              "sub": "Start free, upgrade only if you live in it"},
             {"t": "Learn two shortcuts",
              "sub": "`Cmd+K` to edit, `Cmd+L` to chat. That's 90% of it."},
         ]},

        {"type": "quote", "kicker": "the mindset",
         "quote": "AI won't replace you. A dev who ==wields it== will.",
         "attribution": "every senior right now"},

        {"type": "recap", "kicker": "tl;dr",
         "title": "`editor AI` + `tight prompts` + `AI commits`",
         "body": "Less context-switching. More shipping. ==Steal the setup.=="},

        {"type": "cta", "cmd": "follow --no-hype",
         "title": "Save this for your next ==setup day==.",
         "body": "Real dev workflows + AI tools. No hype.",
         "secondary": "Save this", "primary": "Follow @majdst_codes",
         "site": "majdst.codes"},
    ],
    "caption_body": (
        "Most of the time AI \"saves\" you is lost again switching between a chat tab and your "
        "editor. The unlock isn't a smarter model \u2014 it's pulling the AI into the editor so it "
        "already has your repo context, and giving it tight constraints instead of vague asks. "
        "This is the exact setup (and the refactor prompt) I use daily."),
    "hashtags": [
        "ai", "aitools", "cursor", "aicoding", "developertools", "vscode",
        "webdev", "programming", "coding", "softwareengineering", "devtips",
        "productivity", "codinglife", "developer", "majdstcodes",
    ],
}

if __name__ == "__main__":
    import json
    out = render_carousel(CAROUSEL, out_dir="out_ai")
    print(json.dumps(out, indent=2))
