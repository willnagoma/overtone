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
from data import load_data, build_source_profile, \
    build_concept_lists, build_concept_signal, build_tone_signal, \
    build_brand_safety_signal, build_performance_signal, build_source_signal, \
    build_verdict

# ── ICON MAP ─────────────────────────────────
SIGNAL_ICONS = {
    "Tone":                  "🌡️",
    "Brand Safety":          "🛡️",
    "Audience Concepts":     "📌",
    "Predicted Performance": "📈",
}

def build_stories_for_html(top_n: int = 10) -> list[dict]:
    recs, aw = load_data()

    source_profile                       = build_source_profile(recs)
    positive_concepts, negative_concepts = build_concept_lists(aw)
    concept_signal                       = build_concept_signal(positive_concepts, negative_concepts)

    stories = []

    for _, article in recs.iterrows():
        tone_signal     = build_tone_signal(article, recs)
        bs_signal       = build_brand_safety_signal(article)
        perf_signal     = build_performance_signal(article, recs)
        source_sentence = build_source_signal(article, source_profile)

        signals = [tone_signal, bs_signal, concept_signal, perf_signal]
        verdict = build_verdict(article, signals, source_sentence)

        for sig in signals:
            sig["icon"] = SIGNAL_ICONS.get(sig["name"], "•")

        date_str = article["datepub"].strftime("%-d %b %Y") if pd.notna(article["datepub"]) else ""

        # Clean headline
        headline = article["headline"]
        for suffix in [" - SABC News - Breaking news, special reports, world, business, sport coverage of all South African current events. Africa's news leader.",
                       " | The Citizen", " - TechCentral"]:
            headline = headline.replace(suffix, "").strip()

        stories.append({
            "id":       int(article["id"]) if str(article["id"]).isdigit() else str(article["id"]),
            "headline": headline,
            "source":   article["source_norm"],
            "date":     date_str,
            "url":      article["url"],
            "score":    round(float(article["predicted_performance"]), 7),
            "verdict":  verdict,
            "signals":  signals,
            "concepts": [],
            "matched":  [],
        })

    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:top_n]


def inject_into_html(stories: list[dict], html_path: str) -> bool:
    """
    Finds the const stories = [...]; line in the HTML and replaces
    the array with the new stories data. Returns True if successful.
    """
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

    # 1. Save JSON (for debugging)
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    json_path   = os.path.join(base_dir, "stories_export.json")
    html_path   = os.path.join(base_dir, "overtone_native_widget.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    print(f"✓ Exported {len(stories)} stories to stories_export.json")

    # 2. Inject into HTML
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
    print('  git commit -m "Regenerate widget with latest BQ data"')
    print("  git push")