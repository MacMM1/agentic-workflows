# Job Search Scraper

Given a Find a Job (jobs.service.gov.uk) search results URL, scrapes every matching posting across all pages into a single Excel sheet — title, employer, location, salary, contract type, hours, working pattern, posting/closing dates, a boilerplate-free summary, and links to the posting and its apply page.

Full SOP: [`job_search_scraper.md`](job_search_scraper.md).

## What's here

- `job_search_scraper.md` — the workflow SOP (objective, steps, error handling, verification)
- `scrape_jobs.py` — discovers every job on a search (handling this site's client-rendered pagination), scrapes each posting via the Firecrawl API with a structured extraction schema, and writes the `.xlsx`

## Output lives in `job-search-results/`

One `.xlsx` per search, named from its keywords/location by default.

## Setup

```
pip install -r requirements.txt
```

Needs `requests` and `openpyxl`. Also needs `FIRECRAWL_API_KEY` in `.env` — get a free key at [firecrawl.dev](https://www.firecrawl.dev/) (separate from any Firecrawl MCP connection; this script calls the REST API directly).

## Usage

```
python job-search/scrape_jobs.py --url "https://www.jobs.service.gov.uk/jobs/search?keywords=assistant&location=DA12"
```

Options: `--output PATH`, `--per-page N` (default 30, site max), `--concurrency N` (default 3), `--limit N` (cap jobs scraped, useful for a cheap test run), `--yes` (skip the credit-cost confirmation prompt).
