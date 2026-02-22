# Overtone Explainability Widget
**DSBA 6390 Practicum — Marketing Pod 2**
Brand: Coca-Cola · Market: Japan

---

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## File Structure

```
overtone_app/
├── app.py           ← UI layer (Streamlit) — Willna owns this
├── data.py          ← Data layer (placeholder → BigQuery) — Saketh owns this
├── requirements.txt
└── README.md
```

---

## How to Swap in Real BigQuery Data (Saketh)

Open `data.py` and replace the `get_stories()` function body.

The function must return a `list[dict]` where each dict has this shape:

```python
{
    "id":       int,          # unique story ID
    "headline": str,          # article headline
    "source":   str,          # publication name
    "date":     str,          # display date string e.g. "3 févr. 2026"
    "url":      str,          # full article URL
    "score":    float,        # recommendation_level from BQ (e.g. 0.0999)
    "verdict":  str,          # plain-language explanation (supports **bold**)
    "signals": [              # list of 4 scoring signals
        {
            "icon":   str,    # emoji
            "name":   str,    # signal name e.g. "Brand Mentions"
            "detail": str,    # one-line explanation
            "badge":  str,    # short value label e.g. "3 direct"
            "color":  str,    # "green" | "amber" | "red" | "purple" | "grey"
        },
        ...
    ],
    "concepts": [str, ...],   # all concepts detected in article
    "matched":  [str, ...],   # concepts that matched brand profile
}
```

### BigQuery query template

```python
from google.cloud import bigquery

def get_stories() -> list[dict]:
    client = bigquery.Client()
    query = """
        SELECT
            url,
            headline,
            FORMAT_DATE('%d %b %Y', date_published) AS date,
            source_name,
            recommendation_level,
            tone,
            brand_mentions,
            concepts,
            sentiment_score
        FROM `your_project.overtone_dataset.stories`
        WHERE brand    = 'Coca-Cola'
          AND market   = 'Japan'
          AND date_published BETWEEN '2026-01-25' AND '2026-02-11'
        ORDER BY recommendation_level DESC
        LIMIT 50
    """
    rows = list(client.query(query).result())
    return [build_story_dict(row) for row in rows]


def build_story_dict(row) -> dict:
    # Map BQ columns → widget dict shape
    # You'll need to generate verdict + signals either via:
    #   (a) rule-based logic from BQ columns, OR
    #   (b) a lightweight LLM call per story
    ...
```

---

## Verdict & Signal Generation (Savita)

The `verdict` string and `signals` list can be generated two ways:

**Option A — Rule-based (faster, no API cost)**
Write Python logic that reads `brand_mentions`, `tone`, `sentiment_score`,
`concepts` from BQ and generates the text programmatically.

**Option B — LLM-generated (richer, more natural)**
Pass the BQ row fields to Claude/GPT with a prompt like:
> "Given this article data: {row}, generate a 2-sentence plain-language
> explanation of why this story scored {score} for brand {brand}."

Either works. Start with Option A for the midterm demo.

---

## iFrame Embed (for Overtone)

To embed in Overtone's existing dashboard:

```bash
# Run with specific port
streamlit run app.py --server.port 8502 --server.headless true
```

Then embed via:
```html
<iframe src="http://your-server:8502" width="100%" height="800px"
  frameborder="0" style="border-radius:10px;"></iframe>
```

Or deploy to Streamlit Community Cloud (free) and embed that URL.
