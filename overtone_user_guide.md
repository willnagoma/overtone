# Overtone Explainability Widget — User Guide
**DSBA 6390 Practicum — Marketing Pod 2**  
Client: Razor · Market: South Africa

---

## What Is the Overtone Widget?

The Overtone Explainability Widget shows you **which news articles are most relevant to your brand** and, more importantly, **why** Overtone scored them the way it did. It is built for PR and insights professionals who need to understand and act on coverage data — not read raw numbers.

You do not need to install anything. The widget runs directly in your browser or inside the Overtone dashboard.

**Live link:** https://willnagoma.github.io/overtone/overtone_native_widget.html

---

## Navigating the Widget

The widget has a left sidebar and a top navigation bar with tabs.

### Sidebar
The sidebar shows three sections: **Overview**, **Insights** (currently active), and **Collections**. The widget opens on the Insights page.

### Tabs
At the top of the Insights page you will see four tabs:

| Tab | What it shows |
|---|---|
| **Overview** | Summary view (placeholder) |
| **Monitor** | Relevance score chart + article table — the main view |
| **Moments** | Auto-detected coverage spikes over time |
| **Articles** | Article list (placeholder) |

---

## The Monitor Tab

This is the primary view. It has two parts: a chart at the top and an article table below it.

### Relevance Score Chart

The chart plots each article's **relevance score** (`recommendation_level`) over time. Each dot is one article.

- **Green dots** are high-relevance articles (score ≥ 0.08)
- **Purple dots** are mid-range articles
- **Grey dots** are lower-relevance articles

**Hover** over any dot to see a quick preview of the headline, score, and most notable signal. **Click** a dot to open the full score breakdown popup.

### Article Table

The table lists all articles sorted by relevance score, highest first. Each row shows:

- Headline
- Source URL
- Date published
- Source name
- Relevance score with a visual bar

**Click any row** to open the same score breakdown popup as clicking a chart dot.

---

## The Score Breakdown Popup

Clicking an article (from either the chart or the table) opens a popup with three sections.

### Score Badge
The score is shown as a 7-decimal number (e.g. `0.1458677`). Higher means more relevant to Razor's target audience in South Africa.

### Verdict
A 1–3 sentence plain-language explanation of the score. This is the quickest way to understand what stood out about the article. Example:

> *"Neutral tone is unusual for Mid Non-News content in the last 30 days (typical: Informational). Predicted performance is in the top 0% of articles in the last 30 days."*

### Signal Badges
Four signal badges appear below the verdict, each with a color, icon, name, and short label. These are the four factors that contributed to the score.

| Color | Meaning |
|---|---|
| 🟢 Green | Positive — favorable for brand relevance |
| 🟡 Amber | Caution — something unusual but not harmful |
| 🔴 Red | Flag — tone is shifting, safety risk, or low performance |
| 🟣 Purple | Audience concept — informational, not a flag |
| ⚪ Grey | Neutral — within normal range |

---

## The Four Signals

Every article is evaluated against four signals.

### 🌡️ Tone
Is the article's emotional tone normal for this type of content, or is it shifting?

The system checks whether the dominant tone (Happy, Sad, Angry, Fearful, Hopeful, Informational, etc.) matches the 30-day pattern for this content type. If it has been rising sharply over the past 7 days, the badge turns red. If it is simply different from normal, it turns amber. Grey means everything is typical.

**What this tells you:** A sudden shift toward Fearful or Angry tone across a content type can be an early signal of a narrative change worth monitoring.

### 🛡️ Brand Safety
Does the article contain content that could be harmful to your brand?

The system checks three flags: **Conspiracy**, **Violence**, and **Offensive**. If any are present, the badge turns red and the detail lists all active flags. Green means the article is clean.

**What this tells you:** Even a high-scoring article may not be suitable for amplification if it carries a brand safety flag.

### 📌 Audience Concepts
Does the article align with the concepts that matter most to Razor's affluent target audience?

This signal is audience-level, not per-article. It shows the top concepts weighted highest for Razor's profile (e.g. MTN Group, Standard Bank, South Asia). Purple is informational — it is not a positive or negative flag.

**What this tells you:** Articles that touch high-weight audience concepts are more likely to resonate with your target readers.

### 📈 Predicted Performance
How does this article's predicted reach compare to recent coverage?

The system compares the article's predicted performance score against all articles published in the 30 days before it and expresses this as a percentile rank. Top 10% is green. Bottom 40% is red. Grey means average.

**What this tells you:** A high-performing article is likely to be widely read — making it more important to monitor and respond to if needed.

---

## Article Deepdive

From any popup, click **"Article Deepdive →"** to open a side panel with the full signal breakdown. Each signal is shown with its icon, name, detail sentence, and badge. A **"Read full article →"** button at the bottom links directly to the source.

Use the Deepdive when you want to understand a specific signal in more depth before acting on it.

---

## Submitting a Correction

If you think Overtone scored a signal incorrectly, click **"Did we get it wrong?"** in the popup footer. A short form lets you select what you believe the correct Tone, Brand Safety level, or Predicted Performance category should be. Click **Submit correction** and the feedback is logged for the team to review.

This is how you help improve signal accuracy over time.

---

## The Moments Tab

The Moments tab automatically detects **coverage bursts** — periods where article volume spiked significantly above the recent baseline.

### Moments Chart
The chart shows article counts by day. Purple bars are normal activity. Green bars are days that belong to a detected Moment. A label reading "⚡ Moment · [date]" marks each burst. Click any green bar to jump to that Moment's detail.

### Moment Cards
Below the chart, each detected Moment appears as a card showing:

- Number of articles in the burst
- Sentiment of those articles (Positive / Negative / Mixed)
- Z-score — how many standard deviations above baseline this burst was
- Date window of the burst

Click a card to open the **Moment detail panel** on the right.

### Moment Detail
The detail panel shows the peak date, article count, and z-score, followed by a list of all articles that drove the burst. Click any article in the list to open its full score breakdown popup.

**What this tells you:** A Moment with a high z-score and negative sentiment means a significant amount of unusual coverage appeared quickly — likely something worth investigating or responding to.

---

## Filters and Date Range

At the top of the Monitor and Moments tabs you will see filter controls:

- **Your Filters** shows active source filters (e.g. "All Sources", "businesslive.co.za")
- **Type** lets you switch the chart metric between `recommendation_level`, `overtone_type`, and `sentiment`
- **Date range button** (e.g. "Jan 2025 – Oct 2025 · South Africa") shows the active data window
- **Add a Keyword** input allows keyword filtering (in development)

---

## Understanding the Score

The relevance score (`recommendation_level` / `predicted_performance`) is a decimal number — typically between 0 and 0.15 for this dataset. It reflects how likely the article is to resonate with Razor's affluent South African audience based on Overtone's model.

There is no hard cutoff for "good" or "bad." Instead, focus on **relative position**: an article in the top 10% of the last 30 days is more significant than its raw score suggests.

The score alone does not tell the whole story. Always read the verdict and check the signals — a high-scoring article with a brand safety flag may still require attention.
