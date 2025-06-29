# Nanopub generator for infrastructure tests

## Getting started

This project uses [uv](https://github.com/astral-sh/uv). See [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

Install the project:

```bash
uv sync
```

Then run it like this:

```bash
uv run nanopub_generator --registry-url <url_to_post_nanopubs_to>
```

More options are available:

```bash
uv run nanopub_generator --help
```

## Notes

Do not run this against a production Nanopub Registry. It is intended for testing purposes only.

The code includes a check to make sure that the Registry URL points to Registry in test mode. If it does not, the program will exit with an error message.

ORCID IDs and all other personal data is generated randomly and does not correspond to real people. If there is any overlap with real people, it is purely coincidental.
