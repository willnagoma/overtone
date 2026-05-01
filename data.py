# STEP1
# Open a terminal in VS Code and install all packages: 
# pip install pandas numpy google-cloud-bigquery google-cloud-bigquery-storage db-dtypes

# STEP2
# Install Google Cloud SDK (gcloud):
# Download from cloud.google.com/sdk/docs/install, run the installer, then in the terminal: 
# gcloud init
# gcloud auth application-default login
# Log in with the Google account that has access to capstone-project-400212.

# After STEP 1 AND 2 Run this 

import pandas as pd
import numpy as np
from datetime import timedelta

from google.cloud import bigquery


BQ_PROJECT        = "capstone-project-400212"
BQ_DATASET_MAIN   = "summer2025_chicago"
BQ_DATASET_UNCC   = "uncc"
BQ_TABLE_RECS     = f"{BQ_PROJECT}.{BQ_DATASET_UNCC}.v_recommendations_razor_live_affluent"
BQ_TABLE_AW       = f"{BQ_PROJECT}.{BQ_DATASET_UNCC}.v_articles_razor_affluent_advancedweights"
BQ_TABLE_VERDICTS = f"{BQ_PROJECT}.{BQ_DATASET_MAIN}.verdicts"

client = bigquery.Client(project=BQ_PROJECT)
# Constants

BASELINE_DAYS = 30
TREND_DAYS = 7
MIN_ARTICLES = 5 # min articles for a source to used in signal 5
NEG_THRESHOLD = -0.01 # min weight to surface a negative concept
                      # nothing in advancedweights table reaches this
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

BS_COLS = [
    "brandsafety_id_conspiracy",
    "brandsafety_id_violence",
    "brandsafety_id_offensive",
]

BS_LABELS = {
    "brandsafety_id_conspiracy": "Conspiracy",
    "brandsafety_id_violence": "Violence",
    "brandsafety_id_offensive": "Offensive",
}

SOURCE_MAP = {
    # IOL
    "IOL":                                    "iol.co.za",
    # The Citizen
    "The Citizen":                            "citizen.co.za",
    # BusinessLIVE
    "BusinessLIVE":                           "businesslive.co.za",
    # The South African
    "The South African":                      "thesouthafrican.com",
    # Moneyweb
    "Moneyweb":                               "moneyweb.co.za",
    # Bizcommunity (3 variants)
    "Bizcommunity":                           "bizcommunity.com",
    "Bizcommunity.com":                       "bizcommunity.com",
    # Times LIVE (3 variants)
    "Times LIVE":                             "timeslive.co.za",
    "TimesLIVE":                              "timeslive.co.za",
    # SABC News (2 variants — differs only by escaped apostrophe)
    "SABC News - Breaking news, special reports, world, business, sport coverage of all South African current events. Africa's news leader.":  "sabcnews.com",
    "SABC News - Breaking news, special reports, world, business, sport coverage of all South African current events. Africa\\'s news leader.": "sabcnews.com",
    # Daily Maverick
    "Daily Maverick":                         "dailymaverick.co.za",
    # South Africa Today
    "South Africa Today":                     "southafricatoday.net",
    # BusinessTech
    "BusinessTech":                           "businesstech.co.za",
    # MyBroadband
    "MyBroadband":                            "mybroadband.co.za",
    # Engineering News
    "Engineering News":                       "engineeringnews.co.za",
    # CapeTown ETC
    "CapeTown ETC":                           "capetownetc.com",
    # TechFinancials
    "TechFinancials":                         "techfinancials.co.za",
    # TechCentral
    "TechCentral":                            "techcentral.co.za",
    # EWN
    "EWN":                                    "ewn.co.za",
    "EWN Traffic":                            "ewn.co.za",
    # eNCA
    "eNCA":                                   "enca.com",
    "eNCAnews":                               "enca.com",
    # Sowetan LIVE
    "Sowetan LIVE":                           "sowetanlive.co.za",
    # ITWeb
    "ITWeb":                                  "itweb.co.za",
    # 2oceansvibe
    "2oceansvibe News | South African and international news": "2oceansvibe.com",
    # SA Cricket
    "SA Cricket | OPINION | PLAYERS  | TEAMS  | FEATURES  | SAFFAS ABROAD": "sacricketmag.com",
    # SAPeople
    "SAPeople - Your Worldwide South African Community": "sapeople.com",
    # The Mail & Guardian
    "The Mail & Guardian":                    "mg.co.za",
    # Stuff
    "Stuff":                                  "stuff.co.za",
    # Witness
    "Witness":                                "witness.co.za",
    # The Media Online
    "The Media Online":                       "themediaonline.co.za",
    # news24
    "news24":                                 "news24.com",
    # City Press — no domain variant, keep as is
    # GroundUp News — no domain variant, keep as is
}

# Load data

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """ 
    Load both source tables, parse dates, and apply source normilization.
    Normalization for the source names so that all signal funcitons recieve clean data.
    """
    recs = client.query(f"SELECT * FROM `{BQ_TABLE_RECS}`").to_dataframe()
    aw   = client.query(f"SELECT * FROM `{BQ_TABLE_AW}`").to_dataframe()

    recs["datepub"] = pd.to_datetime(recs["datepub"], format="mixed", errors="coerce")
    recs["source_norm"] = recs["source_name"].replace(SOURCE_MAP)

    return recs, aw

def load_verdicts() -> dict:
    """
    Load pre-generated LLM verdicts from BQ verdicts table.
    Returns a dict keyed by article id for fast lookup in get_stories().
    Falls back to an empty dict if the table is unavailable so build_verdict()
    can be used as a fallback without breaking the app.
    """
    try:
        df = client.query(f"SELECT id, verdict FROM `{BQ_TABLE_VERDICTS}`").to_dataframe()
        return dict(zip(df["id"], df["verdict"]))
    except Exception as e:
        print(f"Warning: could not load verdicts table, falling back to build_verdict(). Error: {e}")
        return {}

def get_reference_date(recs: pd.DataFrame) -> pd.Timestamp:
    """ 
    Use the most recent article date as "today". This will keep logic stable against both CSV and live BQ tables.
    """

    return recs["datepub"].max()


# Pre-compute audience-level lookups
# These are used in multiple signal functions, so we compute them once here and pass them in as needed.

def build_source_profile(recs: pd.DataFrame) -> pd.DataFrame:
    """ 
    For each normalized source with MIN_ARTICLES or more articles, compute what % of their output is each 
    overtone_type.
    Used by Signal 5 (Source Tone).
    """
    source_totals = recs["source_norm"].value_counts()
    reliable = source_totals[source_totals >= MIN_ARTICLES].index
    cross_tab = pd.crosstab(recs["source_norm"], recs["overtone_type"])
    source_type_pct = cross_tab.div(cross_tab.sum(axis=1), axis=0) * 100
    return source_type_pct.loc[source_type_pct.index.isin(reliable)]

def build_concept_lists(aw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """ 
    Split Advanced Weights into positive and negative concept lists.
    Postive threshold = mean + 1 std dev
    Negative threshold = NEG_THRESHOLD (currently set to -0.01, which nothing reaches it)
    Used by signal 3 (Concept Signals).
    """
    mean_w = aw["weight"].mean()
    std_w = aw["weight"].std()
    threshold = mean_w + std_w

    positive = (
        aw[aw["weight"] >= threshold]
        .sort_values("weight", ascending=False)
        .reset_index(drop=True)
    )    
    negative = (
        aw[aw["weight"] < NEG_THRESHOLD]
        .sort_values("weight")
        .reset_index(drop=True)
    )
    return positive, negative


# Signal 1 - Tone/Trend

def build_tone_signal(article: pd.Series, recs: pd.DataFrame) -> dict:
    """
    3 states: 
    Baseline: tone is typical for this overtone_type in the last 30 days
    Deviation: tone differs from the 30-day mode for this type
    Trend: deviation AND the tone has risen >25% relative to the last 7 days

    Windows are anchored to each article's own datepub, with a strict upper
    bound (< art_date) so an article is never included in its own baseline.
    """
    art_date  = article["datepub"]
    cutoff_30 = art_date - timedelta(days=BASELINE_DAYS)
    cutoff_7  = art_date - timedelta(days=TREND_DAYS)
    otype     = article["overtone_type"]

    art_tone_col = article[TONE_COLS].idxmax()
    art_tone_label = TONE_LABELS[art_tone_col]

    baseline = recs[
        (recs["overtone_type"] == otype) &
        (recs["datepub"] >= cutoff_30) &
        (recs["datepub"] < art_date)
    ].copy()
    baseline["_dominant"] = baseline[TONE_COLS].idxmax(axis=1)

    baseline_mode = baseline["_dominant"].mode().iloc[0] if not baseline.empty else None
    baseline_label = TONE_LABELS.get(baseline_mode, baseline_mode)

    pct_30 = (baseline["_dominant"] == art_tone_col).mean() * 100 if not baseline.empty else 0

    window_7 = recs[
        (recs["overtone_type"] == otype) &
        (recs["datepub"] >= cutoff_7) &
        (recs["datepub"] < art_date)
    ].copy()
    window_7["_dominant"] = window_7[TONE_COLS].idxmax(axis=1)
    pct_7 = (window_7["_dominant"] == art_tone_col).mean() * 100 if not window_7.empty else 0

    is_deviation = (baseline_mode is not None) and (art_tone_col != baseline_mode)
    is_trending = is_deviation and (pct_7 > pct_30 * 1.25)

    if is_trending:
        detail = (
            f"{art_tone_label} tone is rising in the last 7 days "
            f"({pct_30:.0f}% -> {pct_7:.0f}% of {otype} articles). "
            f"Typical tone for this type is {baseline_label}."
        )
        color = "red"
    elif is_deviation:
        detail = (
            f"{art_tone_label} tone is unusual for {otype} content "
            f"in the last 30 days (typical: {baseline_label})."
        )
        color = "amber"
    else:
        detail = (
            f"{art_tone_label} tone is typical for {otype} content "
            f"in the last 30 days."
        )
        color = "grey"
    return {
        "name": "Tone",
        "detail": detail,
        "badge": art_tone_label,
        "color": color,

    }


#Signal 2 - Brand Safety

def build_brand_safety_signal(article: pd.Series) -> dict:
    """
    Checks all 3 brand safety columns.
    Shows ALL active flags, not just the worst one. 
    Green when clean, red when any flag is present.
    """
    flags = []
    for col in BS_COLS:
        val = article[col]
        if val != "No Risk":
            flags.append(f"{BS_LABELS[col]}: {val}")

    if flags:
        detail = "Brand safety flags detected: " + " · ".join(flags) + "."
        badge = f"{len(flags)} flag{'s' if len(flags) > 1 else ''}"
        color = "red"
    else:
        detail = "No brand safety flags detected."
        badge = "No flags"
        color = "green"
    return {
        "name": "Brand Safety",
        "detail": detail,
        "badge": badge,
        "color": color,
    }


# Signal 3 - AdvancedWeight Concept Signals


def build_concept_signal(positive_concepts: pd.DataFrame,
                         negative_concepts: pd.DataFrame) -> dict:
    """
    Audience-level signal: not per article for now.
    Shows top 3 high-weight concepts for this audience.
    Negative concepts are currently not surfaced due to low weights, 
    but logic is in place to show them if they reach the NEG_THRESHOLD.
    """
    top3 = positive_concepts.head(3)
    pos_list = ", ".join(top3["category"].tolist())
    detail = f"Top positive concepts: {pos_list}."

    if not negative_concepts.empty:
        neg_list = ", ".join(negative_concepts.head(3)["category"].tolist())
        detail += f" Avoid: {neg_list}."

    top = top3.iloc[0]
    badge = f"{top['category']} ({top['weight_level'].replace(' Positive', '')})"

    return {
        "name": "Audience Concepts",
        "detail": detail,
        "badge": badge,
        "color": "purple",
    }


# Signal 4 - Predicted Performance

def build_performance_signal(article: pd.Series, recs: pd.DataFrame) -> dict:
    """
    Compares this article's predicted_performance to the 30 day baseline.
    Expressed as a percentile rank, more readable than raw values for a PR audience.

    Window is anchored to each article's own datepub, with a strict upper
    bound (< art_date) so an article is never included in its own baseline.
    Returns a grey "No baseline" signal if fewer than MIN_ARTICLES exist in the window.
    """
    art_date  = article["datepub"]
    cutoff_30 = art_date - timedelta(days=BASELINE_DAYS)
    baseline  = recs[
        (recs["datepub"] >= cutoff_30) &
        (recs["datepub"] < art_date)
    ]["predicted_performance"]

    if len(baseline) < MIN_ARTICLES:
        return {
            "name":   "Predicted Performance",
            "detail": "Not enough recent articles to compute a baseline.",
            "badge":  "No baseline",
            "color":  "grey",
        }

    score = article["predicted_performance"]
    percentile = (baseline < score).mean() * 100
    top_pct = max(1, round(100 - percentile))

    if percentile >= 90:
        detail = (
        f"This article is expected to perform better than most recent articles "
        f"based on its predicted performance score. It ranks in the top "
        f"{top_pct}% of articles from the last 30 days, indicating "
        f"high audience engagement potential.")
        badge = f"Top {top_pct}%"
        color = "green"
    elif percentile >= 75:
        detail = (
        f"This article is expected to perform above average compared to recent articles "
        f"based on its predicted performance score. It ranks in the "
        f"{percentile:.0f}th percentile over the last 30 days, suggesting "
        f"good audience engagement potential.")
        badge  = f"{percentile:.0f}th percentile"
        color  = "green"
    elif percentile >= 40:
        detail = (
        f"This article is expected to perform similarly to typical recent articles "
        f"based on its predicted performance score. It ranks in the "
        f"{percentile:.0f}th percentile over the last 30 days, indicating "
        f"moderate audience engagement.")
        badge  = f"{percentile:.0f}th percentile"
        color  = "grey"
    else:
        detail = (
        f"This article is expected to perform lower than most recent articles "
        f"based on its predicted performance score. It ranks in the "
        f"{percentile:.0f}th percentile over the last 30 days, suggesting "
        f"limited audience engagement.")
        badge  = f"{percentile:.0f}th percentile"
        color  = "red"

    return {
        "name": "Predicted Performance",
        "detail": detail,
        "badge": badge,
        "color": color,
        "tooltip": "Predicted performance estimates how well an article is expected to perform compared to recent articles based on audience engagement signals.",
    }


# Signal 5 - Source Tone 

def build_source_signal(article: pd.Series,
                        source_profile: pd.DataFrame) -> dict:
    """
    Returns a short sentence about whether this source typically covers
    this type of content. Folded into verdict rather than a signals slot
    so the 4-slot schema doesn't need to change for v1.
 
    Three states:
      Unusual: source covers this type <10% of the time → amber flag
      Typical:source covers this type >50% of the time → noted
      (silent): anything in between is not worth flagging
    """
    src = article["source_norm"]
    otype = article["overtone_type"]

    if src not in source_profile.index or otype not in source_profile.columns:
        return ""
    
    pct = source_profile.loc[src, otype]
    dom_type = source_profile.loc[src].idxmax()
    dom_pct = source_profile.loc[src].max()

    if pct < 10:
        return(
            f"{src} rarely publishes {otype} content "
            f"({pct:.0f}% of their articles, they mostly cover {dom_type} at {dom_pct:.0f}%)"
        )
    elif pct >= 50:
        return(
            f"{src} commonly publishes {otype} content "
            f"({pct:.0f}% of their articles)."
        )
    return ""



# Verdict Logic

def build_verdict(article: pd.Series, signals: list[dict],
                  source_sentence: str) -> str:
    """
    1-3 sentence plain-language summary for the tooltip.
    Leads with the most notable signal, appends source context if present.
    Falls back to tone detail if nothing notable fires.
    """
    parts = []
 
    tone_sig = next((s for s in signals if s["name"] == "Tone"), None)
    if tone_sig and tone_sig["color"] in ("red", "amber"):
        parts.append(tone_sig["detail"])
 
    bs_sig = next((s for s in signals if s["name"] == "Brand Safety"), None)
    if bs_sig and bs_sig["color"] == "red":
        parts.append(bs_sig["detail"])
 
    perf_sig = next((s for s in signals if s["name"] == "Predicted Performance"), None)
    if perf_sig and perf_sig["color"] in ("green", "red"):
        parts.append(perf_sig["detail"])
 
    if source_sentence:
        parts.append(source_sentence)
 
    # Fallback: tone detail is always present
    if not parts and tone_sig:
        parts.append(tone_sig["detail"])
 
    return " ".join(parts)

# Main Entry Point

def get_stories() -> list[dict]:
    """
    Called by app.py.
    Returns a list of story dicts, unsorted for now pending relevance score
    validation with the team.
    Verdict is looked up from the pre-generated BQ verdicts table by article id.
    Falls back to build_verdict() for any article not found in the verdicts table.
    """
    recs, aw  = load_data()
    verdicts  = load_verdicts()
 
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

        # Use LLM verdict from BQ if available, fall back to rule-based build_verdict()
        verdict = verdicts.get(article["id"]) or build_verdict(article, signals, source_sentence)
 
        date_str = article["datepub"].strftime("%-d %b %Y") if pd.notna(article["datepub"]) else ""
 
        stories.append({
            "id":       article["id"],
            "headline": article["headline"],
            "source":   article["source_norm"],
            "date":     date_str,
            "url":      article["url"],
            "verdict":  verdict,
            "signals":  signals,
        })
 
    return stories


# Quick Test:

if __name__ == "__main__":
    stories = get_stories()

    print(f"Total stories: {len(stories)}")
    print()

    for s in stories[:8]:
        print(f"{s['headline'][:70]}")
        print(f"  Source:  {s['source']}")
        print(f"  Verdict: {s['verdict'][:120]}")
        print(f"  Signals:")
        for sig in s["signals"]:
            print(f"    {sig['name']:25} {sig['badge']:30} {sig['color']}")
        print()
