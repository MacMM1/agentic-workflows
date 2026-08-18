# Job Search Scraper Workflow

## Objective
Given a Find a Job (jobs.service.gov.uk) search results URL, scrape every matching job posting — across all pages — into a single Excel sheet with the fields a job-seeker actually needs to triage: title, employer, location, salary, contract type, hours, working pattern, dates, a short plain-language summary, and links to the posting and its apply page.

## One-Time Setup
1. `pip install -r requirements.txt` (needs `requests` and `openpyxl`, alongside the project's existing dependencies).
2. `FIRECRAWL_API_KEY` set in `.env` — get a key at [firecrawl.dev](https://www.firecrawl.dev/). This is separate from any Firecrawl MCP connection Claude may have; the script calls the Firecrawl REST API directly and needs its own key.

## Inputs
- A Find a Job search results URL (any keywords/location/filters the user has applied in their browser), e.g. `https://www.jobs.service.gov.uk/jobs/search?keywords=assistant&location=DA12`.
- Optional: output path, results-per-page, concurrency, a `--limit` cap for a cheap test run.

## Steps
1. Run the tool:
   ```
   python job-search/scrape_jobs.py --url "<search results URL>"
   ```
2. The script fetches page 1 to read the total result count from "Showing results X to Y of **Z**", then paginates through every listing page (`pageNumber`/`resultsPerPage` query params — this site's pagination is client-rendered, not a plain `page` param) collecting every job's detail URL.
3. It prints the discovered job count and an estimated Firecrawl credit cost, then asks for confirmation before spending credits (skip with `--yes`).
4. For each job URL it calls Firecrawl's `/v2/scrape` with a JSON extraction schema + prompt to pull structured fields plus a 2-3 sentence `simplified_description` (boilerplate about company history/benefits/safeguarding stripped out). Requests run concurrently (default 3 workers) with retry-with-backoff on 429/5xx.
5. Results are written to an `.xlsx` file (default: `job-search-results/<keywords>-<location>.xlsx`) with a bold frozen header row, an autofilter, and clickable hyperlinks in the Job URL / Apply URL columns.

## Outputs
- One `.xlsx` file in `job-search-results/` (or the path passed via `--output`), one row per job posting.
- A console summary of rows written and any job URLs that failed to scrape (with the error), so nothing silently vanishes from the count.

## Verification
- Confirm the printed "found N jobs across P pages" count roughly matches what the site shows for that search.
- Open the `.xlsx` and spot-check a couple of rows against the live posting — especially `closing_date` (only present on the individual job page, not the listing) and that `simplified_description` reads as a fair, boilerplate-free summary rather than a hallucinated one.
- If any jobs failed, decide whether to re-run just those URLs by hand or accept the gap.

## Error Handling
- **`FIRECRAWL_API_KEY is not set`**: add the key to `.env` (see setup) — the script won't fall back to any other credential source.
- **"Could not find a result count on the search page"**: the URL isn't a Find a Job search results page, or the site's markup changed — open the URL in a browser and confirm it's a `jobs/search?...` results listing before retrying.
- **Per-job failures**: logged with the underlying error and skipped rather than aborting the whole run; re-run with just those URLs (via `--url` pointed at a narrower search, or ask the agent to retry them individually) if completeness matters.
- **Site markup changes**: if extraction quality drops (blank fields across the board), the job page's structure has likely changed — re-inspect a sample job page and update `JOB_SCHEMA`/`JOB_PROMPT` in `scrape_jobs.py` accordingly, then note the fix here.
- **Credit cost surprises**: the script estimates ~5 credits per job page (JSON extraction) + 1 credit per listing page and asks for confirmation before spending — if a run needs to stop partway for cost reasons, use `--limit` on a re-run to test cheaply first.
- **429 rate-limit errors**: Firecrawl plans cap requests per minute (the free/starter tier observed was 15/min) — a burst of concurrent scrapes can blow through that in seconds even with retries, since a short fixed backoff doesn't wait out the actual reset window. The script enforces a sliding-window limiter (`--rate-limit`, default 12/min, intentionally a bit under most plans' caps) and parses the server's own "retry after Ns" from 429 responses to wait the right amount rather than guessing. If you're still seeing 429s after a run, lower `--rate-limit` to match your actual plan (check the error body or your Firecrawl dashboard for the real cap) rather than re-running blind.
