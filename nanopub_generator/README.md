# Nanopub generator for infrastructure tests

## Getting started

This project uses [uv](https://github.com/astral-sh/uv). See [installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

Install the project:

```bash
uv sync
```

To run the nanopub generator workload:

```bash
uv run nanopub_generator --mode=registry --registry-url <nanopub_registry_url>
```

To run the query workload:

```bash
uv run nanopub_generator --mode=query --query-url <nanopub_query_url>
```

More options are available:

```bash
uv run nanopub_generator --help
```

Modify the `config.yaml` file to configure the workload parameters.

## Notes

Do not run this against a production Nanopub Registry. It is intended for testing purposes only.

The code includes a check to make sure that the Registry URL points to Registry in test mode. If it does not, the program will exit with an error message.

ORCID IDs and all other personal data is generated randomly and does not correspond to real people. If there is any overlap with real people, it is purely coincidental.
