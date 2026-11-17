# Link Lens

Check HTTP links from a text file and export a CSV report.

Python 3.10+ · standard library only · no installation required.

## Quick start

```sh
python link_lens.py examples/links.txt --output report.csv
```

## Behavior

- Deduplicates URLs and ignores blank lines and `#` comments.
- Follows redirects, tries HEAD first, falls back to GET for 405/501.
- Uses two workers by default, at most four; accepts at most 100 URLs.
- Rejects private/local IP destinations, including redirect destinations.
- Saves status, final URL, and errors to CSV.
- Exits 0 when all responses are below 400, 1 for failed links, 2 for input errors.

A 403 or 429 may reflect a site's automated-client policy rather than a broken link. DNS prechecks are a convenience filter, not a hardened network security boundary. Timeouts apply to individual network operations.

## Development

```sh
python -m unittest discover -s tests -v
```
