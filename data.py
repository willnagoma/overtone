"""
data.py — Overtone Explainability Widget
=========================================
PLACEHOLDER DATA — for UI development only.

When BigQuery access is ready, Saketh replaces
get_stories() with a real BQ query. The shape
of each story dict must stay the same so the
UI renders without any other changes.

BigQuery table expected columns:
  - url             (STRING)
  - headline        (STRING)
  - date_published  (DATE)
  - source_name     (STRING)
  - recommendation_level (FLOAT)
  - tone            (STRING)
  - concepts        (REPEATED STRING or JSON)
  - brand_mentions  (INTEGER)
  - sentiment_score (FLOAT)
"""

# ── SIGNAL COLOR CLASSES ──────────────────────
# Maps to st.markdown badge styling in app.py
GREEN  = "green"
AMBER  = "amber"
RED    = "red"
PURPLE = "purple"
GREY   = "grey"


def get_stories() -> list[dict]:
    """
    Returns a list of story dicts for the widget.

    TO REPLACE WITH BIGQUERY:
    ─────────────────────────
    from google.cloud import bigquery
    client = bigquery.Client()
    query = \"\"\"
        SELECT
            url, headline, date_published, source_name,
            recommendation_level, tone, brand_mentions,
            concepts, sentiment_score
        FROM `your_project.overtone_dataset.stories`
        WHERE brand = 'Coca-Cola'
          AND market = 'Japan'
          AND date_published BETWEEN '2026-01-25' AND '2026-02-11'
        ORDER BY recommendation_level DESC
        LIMIT 50
    \"\"\"
    rows = client.query(query).result()
    return [build_story_dict(row) for row in rows]
    """

    return [
        {
            "id": 0,
            "headline": "Coca-Cola's ¥100M Japan marketing push: inside the summer strategy",
            "source": "Campaign Asia",
            "date": "3 févr. 2026",
            "url": "https://campaignasia.com/coca-cola-japan-summer-strategy",
            "score": 0.0999,
            "verdict": (
                "**Highest-scoring story this period.** Coca-Cola is the primary subject — "
                "strategy coverage that signals market-wide attention. Audience is marketing "
                "professionals watching how Coke moves in Japan ahead of summer."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Primary subject — named throughout",                    "badge": "9 direct",   "color": GREEN},
                {"icon": "🌡️", "name": "Tone",             "detail": "Analytical — strategy coverage, neutral-positive",       "badge": "Positive",   "color": GREEN},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Japan Marketing, Summer Campaign, Brand Strategy, Spend","badge": "4 matched",  "color": GREEN},
                {"icon": "👥", "name": "Audience Fit",     "detail": "Marketing professionals and brand competitors watching", "badge": "Very strong","color": GREEN},
            ],
            "concepts": ["Japan Campaign", "Marketing Strategy", "Summer", "Brand Spend", "Coca-Cola"],
            "matched":  ["Japan Campaign", "Marketing Strategy", "Summer", "Brand Spend", "Coca-Cola"],
        },
        {
            "id": 1,
            "headline": "Summer Sonic 2026 lineup announced — fans react across social and news",
            "source": "Billboard Japan",
            "date": "25 janv. 2026",
            "url": "https://billboardjapan.com/summer-sonic-2026-lineup",
            "score": 0.0921,
            "verdict": (
                "**High-relevance cultural moment.** Summer Sonic is one of Japan's largest "
                "music festivals — exactly the type of event Philip flagged. Audience sentiment "
                "is excited and highly engaged. Strong alignment with Coca-Cola's youth and "
                "lifestyle positioning."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Coca-Cola named as returning festival sponsor",         "badge": "3 direct",   "color": GREEN},
                {"icon": "🌡️", "name": "Tone",             "detail": "High excitement — anticipation and buzz",               "badge": "Positive",   "color": GREEN},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Music Festival, Youth Culture, Sponsorship, Summer",    "badge": "4 matched",  "color": GREEN},
                {"icon": "👥", "name": "Audience Fit",     "detail": "18–34 Japanese consumers — core target demographic",    "badge": "Very strong","color": GREEN},
            ],
            "concepts": ["Music Festival", "Summer Sonic", "Youth Culture", "Sponsorship", "Summer", "Live Events"],
            "matched":  ["Music Festival", "Youth Culture", "Sponsorship", "Summer"],
        },
        {
            "id": 2,
            "headline": "Pepsi Japan refreshes identity ahead of summer — new packaging and celeb tie-in",
            "source": "Ad Age Asia",
            "date": "9 févr. 2026",
            "url": "https://adage.com/asia/pepsi-japan-summer-campaign",
            "score": 0.0867,
            "verdict": (
                "**Direct competitor activation.** Pepsi is moving aggressively in the same "
                "market window Coca-Cola is targeting. High strategic relevance — this story "
                "directly affects campaign positioning decisions."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Pepsi primary, Coca-Cola named as competitive benchmark","badge": "2 indirect", "color": AMBER},
                {"icon": "🌡️", "name": "Tone",             "detail": "Competitive — challenger brand energy",                 "badge": "Neutral",    "color": AMBER},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Pepsi, Competitor, Japan, Summer, Celebrity",           "badge": "4 matched",  "color": GREEN},
                {"icon": "👥", "name": "Audience Fit",     "detail": "Beverage consumers + marketing observers — high overlap","badge": "Strong",    "color": GREEN},
            ],
            "concepts": ["Pepsi Japan", "Competitor", "Summer Campaign", "Celebrity", "Brand Identity"],
            "matched":  ["Competitor", "Summer Campaign", "Brand Identity"],
        },
        {
            "id": 3,
            "headline": "Japan's Gen Z is drinking less soda — health trends reshape beverage market",
            "source": "Toyo Keizai",
            "date": "26 janv. 2026",
            "url": "https://toyokeizai.net/articles/beverage-genz-japan",
            "score": 0.0812,
            "verdict": (
                "**Risk signal requiring attention.** Category-level threat — declining soda "
                "consumption among Coca-Cola's core demographic in Japan. Directly relevant "
                "to campaign timing and messaging strategy."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Coca-Cola cited as category leader at risk",            "badge": "2 direct",   "color": AMBER},
                {"icon": "🌡️", "name": "Tone",             "detail": "Cautionary — market shift, health-first framing",       "badge": "Negative",   "color": RED},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Beverage Market, Gen Z, Health Trends, Japan",          "badge": "4 matched",  "color": GREEN},
                {"icon": "👥", "name": "Audience Fit",     "detail": "Business press + Gen Z consumers — dual audience hit",  "badge": "Strong",     "color": GREEN},
            ],
            "concepts": ["Gen Z Japan", "Health Trends", "Beverage Market", "Soda Decline", "Consumer Shift"],
            "matched":  ["Gen Z Japan", "Health Trends", "Beverage Market", "Consumer Shift"],
        },
        {
            "id": 4,
            "headline": "Tokyo Olympics legacy: how sport sponsorships changed brand perception in Japan",
            "source": "Dentsu Insights",
            "date": "2 févr. 2026",
            "url": "https://dentsu.com/insights/olympics-sponsorship-japan",
            "score": 0.0612,
            "verdict": (
                "Moderate relevance — **sponsorship ROI framing** relevant to Coca-Cola's "
                "ongoing sports and events strategy in Japan. No current campaign mention, "
                "but thematic alignment with brand values is strong."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Named as Olympics sponsor in historical context",       "badge": "1 indirect", "color": AMBER},
                {"icon": "🌡️", "name": "Tone",             "detail": "Analytical — retrospective, evidence-based",            "badge": "Neutral",    "color": GREY},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Sponsorship ROI, Sports, Japan Brand Perception",       "badge": "3 matched",  "color": PURPLE},
                {"icon": "👥", "name": "Audience Fit",     "detail": "Brand strategists and agency professionals",            "badge": "Moderate",   "color": AMBER},
            ],
            "concepts": ["Olympics", "Sponsorship ROI", "Sports Marketing", "Japan", "Brand Perception"],
            "matched":  ["Sponsorship ROI", "Sports Marketing", "Japan"],
        },
        {
            "id": 5,
            "headline": "DJ Snake confirms Tokyo and Osaka dates — biggest Asia tour yet",
            "source": "Consequence of Sound",
            "date": "30 janv. 2026",
            "url": "https://consequenceofsound.net/dj-snake-japan-tour",
            "score": 0.0543,
            "verdict": (
                "Moderate relevance — **DJ alignment opportunity.** Philip specifically "
                "mentioned DJ culture as a potential brand alignment vector in Japan. "
                "No brand mention, but DJ Snake's audience maps closely to Coca-Cola's "
                "18–29 youth target."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Not mentioned — opportunity signal",                   "badge": "0 direct",   "color": GREY},
                {"icon": "🌡️", "name": "Tone",             "detail": "Excited — tour announcement buzz",                     "badge": "Positive",   "color": GREEN},
                {"icon": "📌", "name": "Concept Matches",  "detail": "DJ Culture, Live Events, Youth Audience, Japan Tour",  "badge": "3 matched",  "color": PURPLE},
                {"icon": "👥", "name": "Audience Fit",     "detail": "18–29 Japanese concert-goers — high overlap",          "badge": "Moderate",   "color": AMBER},
            ],
            "concepts": ["DJ Snake", "Tokyo", "Osaka", "Live Events", "DJ Culture", "Asia Tour"],
            "matched":  ["Live Events", "DJ Culture"],
        },
        {
            "id": 6,
            "headline": "Nike x Pharrell Japan collection sells out in 12 minutes — what brands can learn",
            "source": "Nikkei Marketing",
            "date": "27 janv. 2026",
            "url": "https://nikkei.com/marketing/nike-pharrell-japan",
            "score": 0.0478,
            "verdict": (
                "Indirect relevance — **competitor brand alignment signal.** Nike and Pharrell's "
                "Japan launch dominated youth conversation this week. Coca-Cola not mentioned, "
                "but the audience overlap and cultural moment type match tracked campaign targets."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Not mentioned — competitor brand story",               "badge": "0 direct",   "color": GREY},
                {"icon": "🌡️", "name": "Tone",             "detail": "Aspirational — hype and cultural cachet",              "badge": "Positive",   "color": GREEN},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Sneaker Culture, Youth Spending, Brand Alignment",     "badge": "3 matched",  "color": PURPLE},
                {"icon": "👥", "name": "Audience Fit",     "detail": "Streetwear / youth audience — overlaps with Coke target","badge": "Moderate", "color": AMBER},
            ],
            "concepts": ["Sneaker Culture", "Nike", "Pharrell", "Youth Spending", "Brand Alignment", "Japan"],
            "matched":  ["Youth Spending", "Brand Alignment"],
        },
        {
            "id": 7,
            "headline": "Japan vending machine sales hit record high — convenience culture drives growth",
            "source": "Japan Times",
            "date": "4 févr. 2026",
            "url": "https://japantimes.co.jp/business/vending-machine-record",
            "score": 0.0334,
            "verdict": (
                "Low-moderate relevance. **Distribution channel signal** — vending machines "
                "are Coca-Cola's dominant Japan sales channel. Story doesn't mention the brand "
                "but has indirect strategic value for channel planning."
            ),
            "signals": [
                {"icon": "🎯", "name": "Brand Mentions",   "detail": "Not mentioned by name",                                "badge": "0 direct",   "color": GREY},
                {"icon": "🌡️", "name": "Tone",             "detail": "Positive — growth and consumer convenience",           "badge": "Positive",   "color": GREEN},
                {"icon": "📌", "name": "Concept Matches",  "detail": "Vending Machines, Japan Retail, Beverage Distribution","badge": "2 matched",  "color": PURPLE},
                {"icon": "👥", "name": "Audience Fit",     "detail": "General Japan consumer press — broad but shallow",     "badge": "Weak",       "color": GREY},
            ],
            "concepts": ["Vending Machines", "Japan Retail", "Convenience", "Beverage Sales", "Distribution"],
            "matched":  ["Japan Retail", "Beverage Sales"],
        },
    ]


def score_to_label(score: float) -> tuple[str, str]:
    """Returns (label, color_hex) for a given recommendation_level score."""
    if score >= 0.08:
        return "Very High", "#1a7a4a"
    elif score >= 0.06:
        return "High", "#2a5a3a"
    elif score >= 0.04:
        return "Moderate", "#8a6000"
    else:
        return "Low", "#888"
