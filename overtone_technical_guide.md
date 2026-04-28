# Overtone Explainability Widget — Technical Guide
**DSBA 6390 Practicum — Marketing Pod 2**  
Client: Razor · Market: South Africa

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure & Ownership](#file-structure--ownership)
3. [Setup & Installation](#setup--installation)
4. [BigQuery Tables](#bigquery-tables)
5. [data.py — Signal Logic](#datapy--signal-logic)
6. [export_stories.py — Bridge Script](#export_storiespy--bridge-script)
7. [app.py — Streamlit Dev Preview](#apppy--streamlit-dev-preview)
8. [overtone_native_widget.html — Front End](#overtone_native_widgethtml--front-end)
9. [Data Contract](#data-contract)
10. [Pending Work](#pending-work)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
BigQuery (3 tables)
  ├── v_recommendations_razor_live_affluent  →  article records + scores
  ├── data_advancedweights_razor_affluence   →  audience concept weights
  └── verdicts                               →  LLM-generated verdict strings
          ↓
       data.py
       ├── load_data()             — fetches recs + aw from BQ
       ├── load_verdicts()         — fetches LLM verdicts (falls back gracefully)
       ├── build_source_profile()  — per-source tone distribution
       ├── build_concept_lists()   — splits advancedweights into +/- lists
       ├── build_*_signal()        — one function per signal (Signals 1–5)
       ├── build_verdict()         — rule-based fallback verdict
       └── get_stories()           — assembles final list[dict] for callers
          ↓
    export_stories.py              — adds icons, sorts by score, takes top 10
          ↓
    stories_export.json            — paste into HTML widget's const stories = [...]
          ↓
    overtone_native_widget.html    — self-contained, deployed to GitHub Pages
          ↓
    Overtone dashboard iFrame

    app.py                         — Streamlit dev preview (reads data.py directly)
```

The HTML widget is the **production deliverable**. `app.py` is for development and demo purposes only.

---

## File Structure & Ownership

```
overtone_app/
├── overtone_native_widget.html   ← Production deliverable (iFrame-ready)
├── export_stories.py             ← Bridge: data.py → JSON → HTML
├── data.py                       ← Signal logic + BigQuery queries
├── app.py                        ← Streamlit dev preview
├── requirements.txt
└── README.md
```

| File | Owner | Role |
|---|---|---|
| `overtone_native_widget.html` | Willna | UI, iFrame embed, Moments rendering |
| `export_stories.py` | Willna | Bridge script, JSON export, icon map |
| `data.py` | Martha | Signal functions, BQ queries, verdict logic |
| BigQuery tables | Saketh | Table migration, verdicts table population |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Google Cloud SDK (`gcloud`) installed and initialized
- Access to GCP project `capstone-project-400212`

### First-time Setup

```bash
# 1. Install Python packages
pip install pandas numpy google-cloud-bigquery google-cloud-bigquery-storage db-dtypes streamlit plotly

# 2. Install Google Cloud SDK
# Download from cloud.google.com/sdk/docs/install, then:
gcloud init
gcloud auth application-default login
# Log in with the Google account that has access to capstone-project-400212
```

### Regenerate the HTML Widget

Run this whenever the underlying BQ data changes:

```bash
source .venv-overtone/bin/activate
python export_stories.py
# Paste contents of stories_export.json into const stories = [...] in overtone_native_widget.html
git add overtone_native_widget.html
git commit -m "Update with latest data"
git push
```

### Run the Streamlit Dev Preview

```bash
streamlit run app.py
```

---

## BigQuery Tables

| Constant | Full Table Path |
|---|---|
| `BQ_TABLE_RECS` | `capstone-project-400212.summer2025_chicago.v_recommendations_razor_live_affluent` |
| `BQ_TABLE_AW` | `capstone-project-400212.summer2025_chicago.data_advancedweights_razor_affluence` |
| `BQ_TABLE_VERDICTS` | `capstone-project-400212.summer2025_chicago.verdicts` |

All BQ access uses a module-level client:

```python
client = bigquery.Client(project="capstone-project-400212")
```

### Key Columns — Recommendations Table

| Column | Type | Used by |
|---|---|---|
| `id` | int | All — primary key |
| `headline` | str | All signals, verdict, widget |
| `datepub` | datetime | Signal 1, Signal 4, `get_reference_date()` |
| `source_name` | str | `SOURCE_MAP` normalization → `source_norm` |
| `overtone_type` | str | Signal 1 (tone baseline grouping), Signal 5 |
| `predicted_performance` | float | Signal 4, sorting in `export_stories.py` |
| `url` | str | Widget article link |
| `happy_average` … `hopeful_average` | float | Signal 1 — dominant tone detection |
| `brandsafety_id_conspiracy` | str | Signal 2 |
| `brandsafety_id_violence` | str | Signal 2 |
| `brandsafety_id_offensive` | str | Signal 2 |

### Key Columns — Advanced Weights Table

| Column | Type | Used by |
|---|---|---|
| `category` | str | Signal 3 — concept display name |
| `weight` | float | Signal 3 — concept ranking |
| `weight_level` | str | Signal 3 — badge label (e.g. "High Positive") |

---

## data.py — Signal Logic

### Constants

```python
BASELINE_DAYS  = 30     # lookback window for Signal 1 and Signal 4
TREND_DAYS     = 7      # short window for Signal 1 trend detection
MIN_ARTICLES   = 5      # minimum articles for a source to appear in Signal 5
NEG_THRESHOLD  = -0.01  # weight floor for surfacing negative concepts (Signal 3)
```

### `load_data() → tuple[pd.DataFrame, pd.DataFrame]`

Reads both BQ tables, parses `datepub` with `format="mixed"`, and applies `SOURCE_MAP` normalization to produce `source_norm`. Returns `(recs, aw)`.

### `load_verdicts() → dict`

Reads the `verdicts` BQ table and returns a `dict` keyed by article `id`. If the table is unavailable for any reason, it prints a warning and returns `{}` — the pipeline continues using `build_verdict()` as a fallback. No crash.

### `get_reference_date(recs) → pd.Timestamp`

Returns the maximum `datepub` in the dataset. Used to anchor time windows when working against live data where "today" would otherwise move.

### `build_source_profile(recs) → pd.DataFrame`

For each source with at least `MIN_ARTICLES` articles, computes what percentage of their output falls into each `overtone_type`. Used by Signal 5.

### `build_concept_lists(aw) → tuple[pd.DataFrame, pd.DataFrame]`

Splits the advanced weights table into positive and negative concept lists.

- Positive threshold: `mean(weight) + 1 std dev`
- Negative threshold: `NEG_THRESHOLD = -0.01` — currently no concepts reach this, so negative concepts are never surfaced

---

### Signal 1 — Tone (`build_tone_signal`)

**Returns:** dict with `name="Tone"`, badge = dominant tone label, color = grey / amber / red

**Logic:**

1. Find the article's dominant tone column from `TONE_COLS` using `idxmax()`
2. Build a 30-day baseline of articles of the same `overtone_type`, published before this article
3. Find the mode tone in the baseline
4. Compare: if tone matches mode → grey; if different → amber; if different AND the 7-day share of this tone is >25% higher than the 30-day share → red

Windows are anchored to each article's own `datepub` with strict `< art_date` to prevent self-inclusion.

**Tone columns and labels:**

```python
TONE_COLS = [
    "happy_average", "funny_average", "informational_average", "na_average",
    "sad_average", "angry_average", "fearful_average", "hopeful_average",
]
TONE_LABELS = {
    "happy_average": "Happy",
    "funny_average": "Funny",
    "informational_average": "Informational",
    "na_average": "Neutral",
    "sad_average": "Sad",
    "angry_average": "Angry",
    "fearful_average": "Fearful",
    "hopeful_average": "Hopeful",
}
```

---

### Signal 2 — Brand Safety (`build_brand_safety_signal`)

**Returns:** dict with `name="Brand Safety"`, badge = "No flags" or "N flag(s)", color = green / red

**Logic:** Checks all three brand safety columns. Any value other than `"No Risk"` is flagged. All active flags are surfaced in the detail string — not just the worst one.

```python
BS_COLS = [
    "brandsafety_id_conspiracy",
    "brandsafety_id_violence",
    "brandsafety_id_offensive",
]
```

---

### Signal 3 — Audience Concepts (`build_concept_signal`)

**Returns:** dict with `name="Audience Concepts"`, badge = top concept + weight level, color = purple

**Logic:** Audience-level, not per-article. Reads the top 3 concepts from `positive_concepts` (pre-computed from `build_concept_lists()`). Badge shows the top concept and its weight level with "Positive" stripped (e.g. "MTN Group (High)").

Negative concepts are handled in code but not currently surfaced because nothing in the live table reaches `NEG_THRESHOLD = -0.01`.

---

### Signal 4 — Predicted Performance (`build_performance_signal`)

**Returns:** dict with `name="Predicted Performance"`, badge = percentile label, color = green / grey / red

**Logic:** Compares `article["predicted_performance"]` against all articles in the 30 days before it (strict `< art_date`). Expressed as a percentile rank.

| Percentile | Badge | Color |
|---|---|---|
| ≥ 90th | `Top N%` | Green |
| ≥ 75th | `Nth percentile` | Green |
| ≥ 40th | `Nth percentile` | Grey |
| < 40th | `Nth percentile` | Red |
| < `MIN_ARTICLES` in window | `No baseline` | Grey |

---

### Signal 5 — Source Tone (`build_source_signal`)

**Returns:** str (a sentence, not a signal dict)

This signal is folded into the verdict text rather than occupying a slot in the four-signal schema, to avoid a schema change in v1.

**Logic:** Looks up the article's normalized source in `source_profile`. If the source covers this `overtone_type` less than 10% of the time → flags as unusual. If 50%+ → notes as typical. Between 10–50% → silent.

Requires the source to have at least `MIN_ARTICLES = 5` articles in the dataset.

---

### `build_verdict(article, signals, source_sentence) → str`

Rule-based fallback verdict. Assembles 1–3 sentences from signal outputs in priority order:

1. Tone detail — if red or amber
2. Brand Safety detail — if red
3. Predicted Performance detail — if green or red
4. Source sentence — if non-empty
5. Tone detail — unconditional fallback if nothing else fired

---

### `get_stories() → list[dict]`

Main entry point called by `app.py`. Calls `load_verdicts()` first, then iterates over all articles in `recs`. For each article, verdict is looked up from the BQ verdicts dict by `article["id"]`. Falls back to `build_verdict()` for any article not found.

Signal icons (`🌡️`, `🛡️`, `📌`, `📈`) are **not** added by `data.py` — they are added by `export_stories.py` for the HTML widget, or rendered directly in `app.py`'s HTML templates.

---

## export_stories.py — Bridge Script

Adds the `"icon"` key to each signal dict (required by the HTML widget), sorts all stories by `predicted_performance` descending, takes the top N (default 10), and writes to `stories_export.json`.

```python
SIGNAL_ICONS = {
    "Tone":                  "🌡️",
    "Brand Safety":          "🛡️",
    "Audience Concepts":     "📌",
    "Predicted Performance": "📈",
}
```

The date string is formatted as `"%-d %b %Y"` (e.g. `"1 Apr 2025"`) using `strftime`.

`concepts` and `matched` are written as empty lists (`[]`) — these fields are placeholders pending a future BQ column that maps article-level concepts.

Run with:

```bash
python export_stories.py
```

Outputs `stories_export.json`. Console prints a top-5 preview with scores, sources, and truncated verdicts.

---

## app.py — Streamlit Dev Preview

`app.py` is a development-only UI. It is **not** the production deliverable.

It calls `get_stories()` and `score_to_label()` directly from `data.py` and renders the same signal cards using Streamlit's `st.markdown()` with inline HTML/CSS. Interactive chart is built with Plotly (`plotly.graph_objects`). Click events on chart points use `st.plotly_chart(on_select="rerun")` and are handled via `st.session_state.selected_id`.

Score tiers from `score_to_label()`:

| Score | Label | CSS class |
|---|---|---|
| ≥ 0.08 | HIGH | `score-high` |
| ≥ 0.04 | MEDIUM | `score-medium` |
| < 0.04 | LOW | `score-low` |

Note: the context header in `app.py` currently reads `"Brand: Coca-Cola · Market: Japan"` — this should be updated to `"Brand: Razor · Market: South Africa"` before any demo.

---

## overtone_native_widget.html — Front End

A single, fully self-contained HTML file with no external runtime dependencies (only Google Fonts). All data is baked into a `const stories = [...]` JavaScript array at the bottom of the file.

### Tabs

Tab switching is handled by `switchTab(name)`, which toggles `.active` CSS classes on `.subtab` and `.tab-panel` elements. Switching to `"moments"` also calls `renderMomentsChart()`.

### Monitor Tab

`renderMonitorChart()` builds an SVG line chart from the `stories` array, sorted by `datepub`. Points are rendered as `<circle>` elements with `data-story` attributes. Click events call `triggerGraph(e, id)` → `openPopup(id, anchorEl, 'graph')`.

### Popup

`openPopup(id, anchorEl, src)` populates the popup with verdict text, score badge, and four signal badge pills (`.signal-badge-pill`). `positionPopup()` handles smart positioning — popup opens above the anchor if there is room, below otherwise.

The popup has three internal views toggled by CSS class:
- `#popup-normal-view` — score, verdict, signal badges
- `#popup-feedback-view` — correction form
- `#popup-confirmation-view` — post-submit confirmation

### Deepdive Panel

`openDeepdive()` opens a side panel positioned to the right of the popup (or left if not enough room). Shows full signal rows with icon, name, detail, and badge. Links to the article URL via `#dd-article-link`.

### Feedback Form

`submitFeedback()` logs the correction to `console.log` with this shape:

```javascript
{
  article_id:      int,
  submitted_at:    ISO string,
  tone_computer:   str,
  tone_human:      str,
  safety_computer: str,
  safety_human:    str,
  perf_computer:   str,
  perf_human:      str,
}
```

BQ write-back is not yet implemented — feedback is currently console-only.

### Moments Tab

**`buildTimeline(storiesArr)`** — buckets articles by day into a dense day-by-day array spanning the full date range. Days with no articles get `count: 0`.

**`detectMoments(timeline, window=3, threshold=1.5, minCount=2)`** — z-score based burst detection:

1. For each day `i`, compute mean and std of the `window` days before it
2. Spike if `z ≥ threshold` AND `count ≥ minCount` (or `count ≥ minCount` when std = 0)
3. Merge adjacent spike days (gap ≤ 1 day) into single Moment windows
4. Each Moment gets: label, peakDate, windowStr, articleCount, cumulative strength score, max z-score, sentiment

Sentiment is derived from the tone signal colors of articles in the Moment: majority red → negative, any green + no red → positive, otherwise mixed.

**`renderMomentsChart()`** — SVG bar chart. Baseline bars are `rgba(108,99,224,0.28)`. Moment bars are `#1a8a52`. A dashed green rectangle spans the full Moment window. A green label badge (`⚡ Moment · [date]`) appears at the peak.

**`renderMomentList()`** — renders clickable Moment cards. Each card shows article count, sentiment pill, z-score pill, and date window.

**`openMomentDetail(idx)`** — renders a detail panel showing peak date, article count, z-score stats, and all articles in the Moment as clickable rows that open `openPopup()`.

### CSS Variables

All colors are defined as CSS custom properties on `:root`:

```css
--purple:       #6c63e0;
--green:        #1a8a52;
--green-bg:     #eaf6f0;
--amber:        #8a6000;
--amber-bg:     #fef8e6;
--red:          #c0392b;
--red-bg:       #fdecea;
--text-primary: #1a1a2e;
--text-muted:   #9898b0;
```

---

## Data Contract

`export_stories.py` and the HTML widget share this schema. Any change to this shape requires updates in both files.

```python
{
    "id":       int,
    "headline": str,
    "source":   str,         # normalized e.g. "businesslive.co.za"
    "date":     str,         # "%-d %b %Y" e.g. "1 Apr 2025"
    "url":      str,
    "score":    float,       # predicted_performance
    "verdict":  str,         # 1-3 sentence plain-language explanation
    "signals": [
        {
            "icon":   str,   # emoji added by export_stories.py
            "name":   str,
            "detail": str,
            "badge":  str,
            "color":  str,   # "green" | "amber" | "red" | "purple" | "grey"
        },
        # exactly 4 signals
    ],
    "concepts": [str],       # placeholder — empty list in current version
    "matched":  [str],       # placeholder — empty list in current version
}
```

Note: `app.py`'s `get_stories()` output does **not** include `"score"`, `"concepts"`, or `"matched"` — those are added by `export_stories.py` for the HTML widget only.

---

## Pending Work

### Saketh — BigQuery Migration
`load_data()` already queries BigQuery. If any schema change is made to the live BQ table, verify that `TONE_COLS`, `BS_COLS`, and `SOURCE_MAP` still match the actual column names. Run `python data.py` to check — expect 8 stories with signals and verdicts printed.

### Martha — LLM Verdict Layer
`load_verdicts()` and the lookup in `get_stories()` are already wired. Once the `verdicts` table is populated via the Gemini Flash query (see README), `build_verdict()` becomes the fallback only.

Target BQ SQL for verdict generation:
```sql
SELECT
  id,
  ML.GENERATE_TEXT(
    MODEL `overtone-366714.globalnewsgaps.gemini_flash_2_5`,
    STRUCT(
      CONCAT(
        'In 2 plain sentences, explain why this article scored ',
        CAST(recommendation_level AS STRING),
        ' for a PR firm tracking brand relevance. ',
        'Article headline: ', headline, '. ',
        'Tone: ', overtone_type, '.'
      ) AS prompt
    )
  ).ml_generate_text_llm_result AS verdict
FROM `overtone-dev.capstone.recommendations`
```

### Feedback Write-Back
`submitFeedback()` in the HTML widget currently logs to console only. A backend endpoint or BQ streaming insert is needed to persist corrections.

### Article-Level Concepts
`concepts` and `matched` arrays in the data contract are empty placeholders. These will be populated once article-level concept tagging is available from BQ.

### Keyword Filter
The "Add a Keyword" input in the widget UI is present but not wired to any filtering logic.

### Context Header in app.py
The header in `app.py` reads `"Brand: Coca-Cola · Market: Japan"`. Update to `"Brand: Razor · Market: South Africa"` before any external demo.

---

## Troubleshooting

**`KeyError` on a tone or brand safety column**  
The live BQ table schema has changed. Check `TONE_COLS` and `BS_COLS` in `data.py` against actual BQ column names.

**`No baseline` on most Signal 4 outputs**  
Fewer than `MIN_ARTICLES = 5` records exist in the 30-day window before those articles. Expected for early or sparse data. Lower `MIN_ARTICLES` temporarily if needed.

**Verdicts not loading from BQ**  
`load_verdicts()` will warn and fall back to `build_verdict()`. Check that the `verdicts` table exists and your GCP account has read access to `capstone-project-400212`.

**`gcloud` auth error**  
```bash
gcloud auth application-default login
```

**Moments tab shows "No moments detected yet"**  
`detectMoments()` requires at least `minCount = 2` articles on a spike day and a z-score ≥ 1.5. With only 10 articles baked into the current widget, the detection window is very short. Add more data or lower `threshold` in `detectMoments()`.

**HTML widget not updating after export**  
`export_stories.py` writes `stories_export.json` but does not automatically patch the HTML file. Manually replace the `const stories = [...]` array in `overtone_native_widget.html` with the new JSON contents, then push to GitHub.

**Source missing from Signal 5**  
The source needs at least `MIN_ARTICLES = 5` articles in the dataset to be included in `build_source_profile()`. Below this threshold, Signal 5 is silently omitted from the verdict.
