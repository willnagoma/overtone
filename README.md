# Overtone Explainability Widget
**DSBA 6390 Practicum — Marketing Pod 2**  
Client: Razor · Market: South Africa

---

## What This Is

An iFrame-ready HTML explainability module for Overtone's brand relevance scoring system. It surfaces why a story was scored the way it was — making Overtone's signal logic readable for non-technical PR and insights professionals.

Live demo: **https://willnagoma.github.io/overtone/overtone_native_widget.html**

---

## File Structure

```
overtone_app/
├── overtone_native_widget.html  ← Final deliverable (iFrame-ready) — Willna owns this
├── export_stories.py            ← Bridge script: runs data pipeline → updates HTML — Willna owns this
├── data.py                      ← Signal logic (CSV → BigQuery) — Martha owns this
├── data_sample.py               ← Original placeholder data (for reference only)
├── recommendations.csv          ← Real Overtone article data
├── advancedweights.csv          ← Audience concept weights
├── requirements.txt
└── README.md
```

---

## How to Run the Pipeline

Every time the data changes, regenerate the HTML with:

```bash
# 1. Activate virtual environment
source .venv-overtone/bin/activate

# 2. Install dependencies (first time only)
pip install -r requirements.txt

# 3. Run the bridge script — updates overtone_native_widget.html automatically
python export_stories.py

# 4. Push to GitHub — live link updates
git add overtone_native_widget.html
git commit -m "Update with latest data"
git push
```

---

## Architecture

```
recommendations.csv + advancedweights.csv
           ↓
       data.py  (Martha — signal logic)
           ↓
   export_stories.py  (Willna — bridge script)
           ↓
 overtone_native_widget.html  (baked in, self-contained)
           ↓
    GitHub Pages → iFrame embed in Overtone dashboard
```

---

## Saketh — BigQuery Migration

**Task:** Swap `load_data()` in `data.py` from reading CSVs to reading from BigQuery.

Current CSV-based version:
```python
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    recs = pd.read_csv(RECS_PATH)
    aw   = pd.read_csv(WEIGHTS_PATH)
    ...
```

Target BigQuery version:
```python
from google.cloud import bigquery

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    client = bigquery.Client()

    recs = client.query("""
        SELECT *
        FROM `overtone-dev.capstone.recommendations`
    """).to_dataframe()

    aw = client.query("""
        SELECT *
        FROM `overtone-dev.capstone.advancedweights`
    """).to_dataframe()

    recs["datepub"] = pd.to_datetime(recs["datepub"], format="mixed", errors="coerce")
    recs["source_norm"] = recs["source_name"].replace(SOURCE_MAP)

    return recs, aw
```

After swapping, verify all signals still produce output by running:
```bash
python data.py
```

Expected output: stories printed with signals and verdicts. If any signal throws an error, the column name likely differs between the CSV and the live BQ table — check and update accordingly.

---

## Martha — LLM Verdict Layer

**Task:** Replace the rule-based `build_verdict()` with LLM-generated plain language strings stored as a BQ column.

Target query using Gemini Flash:
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

Once verdict strings are stored as a BQ column, update `build_verdict()` in `data.py` to read from that column instead of computing it.

---

## Data Contract

`export_stories.py` expects `data.py` to return a `list[dict]` from `get_stories()` where each dict has this shape:

```python
{
    "id":       int,
    "headline": str,
    "source":   str,        # normalized source name e.g. "businesslive.co.za"
    "date":     str,        # display string e.g. "1 Apr 2025"
    "url":      str,
    "score":    float,      # recommendation_level value e.g. 0.1458
    "verdict":  str,        # plain-language explanation (2 sentences max)
    "signals": [
        {
            "icon":   str,  # emoji e.g. "🌡️"
            "name":   str,  # e.g. "Tone"
            "detail": str,  # one-line explanation
            "badge":  str,  # short label e.g. "Informational"
            "color":  str,  # "green" | "amber" | "red" | "purple" | "grey"
        },
        ...                 # exactly 4 signals per story
    ],
    "concepts": [str, ...], # article-level concepts (placeholder until item 4)
    "matched":  [str, ...], # concepts matching brand profile
}
```

---

## iFrame Embed (for Overtone)

The widget is a single self-contained HTML file — no server required.

```html
<iframe
  src="https://willnagoma.github.io/overtone/overtone_native_widget.html"
  width="100%"
  height="800px"
  frameborder="0"
  style="border-radius:10px;">
</iframe>
```

For production, host the HTML file on Overtone's own infrastructure and update the `src` URL accordingly.
