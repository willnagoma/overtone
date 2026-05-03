"""
export_stories.py
==================
Bridge script: runs Martha's data.py logic, adds missing fields,
takes top 10 by predicted_performance, and automatically injects
the data into overtone_native_widget.html.

Run with:
    python export_stories.py

Output:
    stories_export.json        (intermediate — for debugging)
    overtone_native_widget.html (updated automatically)
"""

import json
import sys
import os
import re
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from data import get_stories, load_data

# ── ICON MAP ─────────────────────────────────
SIGNAL_ICONS = {
    "Tone":                  "🌡️",
    "Brand Safety":          "🛡️",
    "Audience Concepts":     "📌",
    "Predicted Performance": "📈",
}

def build_stories_for_html(top_n: int = 10) -> list[dict]:
    # Use get_stories() so LLM verdicts from BQ flow through
    stories = get_stories()

    # Load scores separately so we can sort
    recs, _ = load_data()
    score_lookup = dict(zip(recs["id"].astype(str), recs["predicted_performance"]))

    enriched = []
    for s in stories:
        # Clean headline
        headline = s["headline"]
        for suffix in [
            " - SABC News - Breaking news, special reports, world, business, sport coverage of all South African current events. Africa's news leader.",
            " | The Citizen",
            " - TechCentral"
        ]:
            headline = headline.replace(suffix, "").strip()

        # Add icons to signals
        for sig in s["signals"]:
            sig["icon"] = SIGNAL_ICONS.get(sig["name"], "•")

        score = float(score_lookup.get(str(s["id"]), 0))

        enriched.append({
            "id":       int(s["id"]) if str(s["id"]).isdigit() else str(s["id"]),
            "headline": headline,
            "source":   s["source"],
            "date":     s["date"],
            "url":      s["url"],
            "score":    round(score, 7),
            "verdict":  s["verdict"],  # LLM verdict from BQ if available
            "signals":  s["signals"],
            "concepts": [],
            "matched":  [],
        })

    enriched.sort(key=lambda x: x["score"], reverse=True)
    return enriched[:top_n]


def inject_into_html(stories: list[dict], html_path: str) -> bool:
    if not os.path.exists(html_path):
        print(f"✗ HTML file not found: {html_path}")
        return False

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    js_stories = json.dumps(stories, ensure_ascii=False)
    new_html = re.sub(
        r'const stories = \[.*?\];',
        f'const stories = {js_stories};',
        html,
        flags=re.DOTALL
    )

    if new_html == html:
        print("✗ Could not find 'const stories = [...]' in HTML — injection skipped.")
        return False

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    return True


if __name__ == "__main__":
    print("Building stories from real data...")
    stories = build_stories_for_html(top_n=10)

    base_dir  = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "stories_export.json")
    html_path = os.path.join(base_dir, "overtone_native_widget.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    print(f"✓ Exported {len(stories)} stories to stories_export.json")

    if inject_into_html(stories, html_path):
        print(f"✓ Injected into overtone_native_widget.html")
    else:
        print("  Manual step: paste stories_export.json into the HTML's const stories = [...] array.")

    print()
    print("Top 5 preview:")
    for s in stories[:5]:
        print(f"  [{s['score']:+.4f}] {s['headline'][:65]}")
        print(f"           {s['source']} · {s['date']}")
        print(f"           Verdict: {s['verdict'][:90]}...")
        print()
    print("Pipeline complete. Run:")
    print("  git add overtone_native_widget.html")
    print('  git commit -m "Regenerate widget with latest BQ data + LLM verdicts"')
    print("  git push")
