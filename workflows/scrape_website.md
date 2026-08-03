# Scrape Website Workflow

## Objective
Collect page content from a target website and save the result to the temporary working area.

## Inputs
- target URL
- output filename
- optional headers or cookies

## Steps
1. Validate the input URL.
2. Fetch the page using a deterministic tool.
3. Save the raw response to `.tmp/`.
4. Normalize or parse the content if needed.

## Outputs
- a saved source artifact in `.tmp/`
- any extracted content needed downstream

## Verification
- confirm the destination file exists
- confirm the response is non-empty
- confirm the parsed result looks usable
