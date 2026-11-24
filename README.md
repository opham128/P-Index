# p-Index Calculator

A web app for computing the **p-Index**, a scientometric indicator of a scholar's propensity for thought leadership, as proposed by Pham, Wu, and Wang (2024) in the *Journal of Consumer Research*.

Live at: [p-index.net](https://www.p-index.net)

---

## What is the p-Index?

The p-Index is the average citation percentile rank of a researcher's published articles relative to other articles published **the same year in the same journals**. It controls for seniority effects and reflects how consistently a researcher's work outperforms the venues where they publish.

> Pham, Michel Tuan, Alisa Yinghao Wu, and Danqi Wang (2024), "Benchmarking Scholarship in Consumer Research: The p-Index of Thought Leadership," *Journal of Consumer Research*, Vol. 51(1), 191–203.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | HTML/CSS/JS (static) |
| Backend | Python (Flask) |
| API | Web of Science (WoS) REST API |
| Database | Neon (Postgres on Vercel) |
| Hosting | Vercel |

---

## How It Works

### API Flow

1. User searches by researcher name → `/api/search` queries WoS for matching researcher profiles
2. User selects a profile → `/api/papers` fetches the researcher's full publication list
3. User deselects irrelevant papers and hits Calculate → `/api/calculate` computes the p-Index

### p-Index Computation (`framework/pindex.py`)

For each paper, the app fetches all articles published in the same journal and year from WoS, then computes the paper's citation percentile rank within that set.

Two scores are returned:
- **PI** — raw p-Index (mean percentile rank across all selected papers)
- **OWPI** — authorship-weighted p-Index, giving more weight to papers where the researcher is lead/sole author, using the Abbas (2011) weighting formula

### Caching Strategy

The most expensive operation is fetching citation distributions for each (journal, year) pair. To minimize WoS API calls:

- Each (journal, year) cell is stored in Neon as a serialized array of citation counts
- On any new request, the cache is checked first — if a valid entry exists and is **less than 7 days old**, it's reused
- Otherwise the cell is re-fetched from WoS and the cache is updated

This means a researcher with 30 papers across 15 journals requires at most 15 WoS bulk queries instead of 30+, and subsequent researchers publishing in the same journals hit the cache entirely.

### Storage Efficiency

Rather than storing full paper records per journal/year, only the **citation count array** is stored per cell. This keeps the database footprint small while still supporting percentile rank calculations for any researcher queried against that cell.

---

## Project Structure

