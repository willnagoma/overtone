"""
export_stories.py
==================
Bridge script: runs Martha's data.py logic, adds missing fields,
takes top 10 by predicted_performance, exports as JSON ready to
paste into the HTML widget's stories array.

Run with:
    python export_stories.py

Output:
    stories_export.json
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from data import load_data, build_source_profile, \
    build_concept_lists, build_concept_signal, build_tone_signal, \
    build_brand_safety_signal, build_performance_signal, build_source_signal, \
    build_verdict

# ── ICON MAP ─────────────────────────────────
# Maps signal names to emojis for the HTML widget
SIGNAL_ICONS = {
    "Tone":                 "🌡️",
    "Brand Safety":         "🛡️",
    "Audience Concepts":    "📌",
    "Predicted Performance":"📈",
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

        # Add icons (missing from Martha's output)
        for sig in signals:
            sig["icon"] = SIGNAL_ICONS.get(sig["name"], "•")

        date_str = article["datepub"].strftime("%-d %b %Y") if pd.notna(article["datepub"]) else ""

        stories.append({
            "id":       str(article["id"]),
            "headline": article["headline"],
            "source":   article["source_norm"],
            "date":     date_str,
            "url":      article["url"],
            "score":    round(float(article["predicted_performance"]), 7),
            "verdict":  verdict,
            "signals":  signals,
            "concepts": [],   # not in CSV — placeholder for now
            "matched":  [],   # not in CSV — placeholder for now
        })

    # Sort by score descending, take top N
    stories.sort(key=lambda x: x["score"], reverse=True)
    return stories[:top_n]


if __name__ == "__main__":
    print("Building stories from real data...")
    stories = build_stories_for_html(top_n=10)

    output_path = os.path.join(os.path.dirname(__file__), "stories_export.json")
    with open(output_path, "w") as f:
        json.dump(stories, f, indent=2)

    print(f"✓ Exported {len(stories)} stories to stories_export.json")
    print()
    print("Top 5 preview:")
    for s in stories[:5]:
        print(f"  [{s['score']:+.4f}] {s['headline'][:65]}")
        print(f"           {s['source']} · {s['date']}")
        print(f"           Verdict: {s['verdict'][:90]}...")
        print()
    print("Next step: paste the contents of stories_export.json into")
    print("the HTML widget's `const stories = [...]` array.")
