from carousel_engine import render_carousel

CAROUSEL = {
    "handle": "@majdst_codes",
    "site": "majdst.codes",
    "slug": "delete-every-ngif",
    "title": "Delete every *ngIf",
    "slides": [
        {
            "type": "hook",
            "kicker": "Angular",
            "cmd": "rm -rf *ngIf *ngFor *ngSwitch",
            "title": "Delete every `*ngIf` in your Angular app.",
        },
        {
            "type": "text",
            "kicker": "why",
            "title": "Angular 17 shipped ==built-in control flow==",
            "body": "No structural directives. No `CommonModule` import. Same logic — cleaner templates and faster rendering.",
        },
        {
            "type": "code",
            "filename": "list.component.html",
            "lang": "html",
            "label": "BEFORE",
            "title": "The old way",
            "code": """<div *ngIf="user(); else loading">
  Welcome, {{ user().name }}
</div>

<ng-template #loading>
  <app-spinner />
</ng-template>""",
        },
        {
            "type": "code",
            "filename": "list.component.html",
            "lang": "html",
            "label": "AFTER",
            "title": "The new way",
            "code": """@if (user(); as u) {
  <div>Welcome, {{ u.name }}</div>
} @else {
  <app-spinner />
}""",
            "note": "Same output. Half the noise. No `#templateRef` gymnastics.",
        },
        {
            "type": "code",
            "filename": "todos.component.html",
            "lang": "html",
            "label": "AFTER",
            "title": "And `*ngFor` becomes `@for`",
            "code": """@for (todo of todos(); track todo.id) {
  <li>{{ todo.title }}</li>
} @empty {
  <p>Nothing left to do</p>
}""",
            "note": "`track` is now ==required== — it kills a whole class of rendering bugs.",
        },
        {
            "type": "list",
            "kicker": "payoff",
            "title": "Why it actually wins",
            "items": [
                {"t": "Faster rendering", "sub": "less directive overhead, lighter change detection"},
                {"t": "Zero imports", "sub": "control flow is built into the template compiler"},
                {"t": "track is mandatory", "sub": "fixes the silent *ngFor performance footgun"},
                {"t": "Reads like real code", "sub": "if / for / switch — not directives in disguise"},
            ],
        },
        {
            "type": "recap",
            "kicker": "tl;dr",
            "title": "`@if` · `@for` · `@switch`",
            "body": "Built in. Faster. Cleaner. ==Ship it.==",
        },
        {
            "type": "cta",
            "cmd": "follow --topic angular --no-hype",
            "title": "Save this for your next ==refactor==.",
            "body": "I post real-world dev patterns straight from production work. No hype.",
            "secondary": "Save this",
            "primary": "Follow @majdst_codes",
            "site": "majdst.codes",
        },
    ],
    "caption_body": "Angular's built-in control flow (@if / @for / @switch) landed in v17 and is stable now. It replaces *ngIf, *ngFor and *ngSwitch — no CommonModule, less boilerplate, and `track` is required so you stop shipping silent list-rendering bugs.\n\nSwipe through for the before/after. Which one are you still using *ngIf in? ",
    "hashtags": [
        "angular", "angulardev", "angular17", "typescript", "javascript",
        "webdevelopment", "frontend", "frontenddeveloper", "webdev", "coding",
        "programming", "devtips", "softwareengineer", "codenewbie", "100daysofcode",
    ],
}

if __name__ == "__main__":
    import json
    out = render_carousel(CAROUSEL, out_dir="out", keep_html=False)
    print(json.dumps(out, indent=2))
