import argparse
from concurrent.futures import ProcessPoolExecutor
import httpx
import schedule
import time
import yaml

from generator import NanopubGenerator
from query import fetch, run_query_user

parser = argparse.ArgumentParser(description="Nanopub generator")
parser.add_argument(
    "--registry-url",
    help="URL of the Registry endpoint for publishing nanopubs. Required if not in dry-run mode and mode set to registry.",
)
parser.add_argument(
    "--query-url",
    help="URL of the Query endpoint. Required if mode set to query.",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="If set, do not actually publish nanopubs, just print what would be published",
)
parser.add_argument(
    "--config-file",
    type=str,
    help="Path to a configuration file (config.yaml) for the generator. Default: ./config.yaml",
    default="./config.yaml",
)
parser.add_argument(
    "--mode",
    type=str,
    help="Mode for generator pipeline. Possbile values: registry, query. Default: query",
    default="query",
)


def verify_test_instance(url: str) -> None:
    """Verify that the provided URL points a test instance of the Nanopub Registry."""
    print(f"Verifying that {url} is a test instance of the Nanopub Registry...")
    r = httpx.get(url)
    assert r.status_code == 200, (
        f"Failed to connect to {url}, status code: {r.status_code}"
    )
    assert "Nanopub-Registry-Test-Instance" in r.headers, (
        f"{url} is not a Nanopub Registry"
    )
    assert r.headers["Nanopub-Registry-Test-Instance"] == "true", (
        f"{url} is not a test instance of the Nanopub Registry"
    )


def run():
    args = parser.parse_args()
    try:
        with open(args.config_file, "rt") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"Configuration file not found: {e}")
        return 1
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error reading configuration file: {e}")
        return 1

    print(f"Using configuration from {args.config_file}")

    if args.mode == "registry":
        if not args.dry_run:
            # Verify the registry URL
            if not args.registry_url:
                print("Error: --registry-url is required when not in dry-run mode.")
                return 1
            try:
                verify_test_instance(args.registry_url)
            except Exception as e:
                print(f"Error verifying registry URL: {e}")
                return 1

        generator = NanopubGenerator(config, args)
        # Schedule the nanopub publishing task
        schedule.every(config["generator"]["post_interval"] / 1000).seconds.do(
            generator.publish_nanopub_safe,
        )

        print("Nanopub generator started. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(1)

    if args.mode == "query":
        if not args.query_url:
            print("Error: --query-url is required when query mode is used.")
            return 1
        # Fetch pubkeys
        pubkeys = fetch(args.query_url, "pubkey")
        # Transform pubkeys to endpoints
        pubkeys = [f"{args.query_url}/repo/pubkey/{pubkey}" for pubkey in pubkeys]
        custom_endpoints = {}  # Add additional endpoints along with probability of querying each
        for query, prob in config["query"]["probabilities_endpoints"].items():
            custom_endpoints.update({f"{args.query_url}/repo/{query}": prob})
        with ProcessPoolExecutor(  # Assign and run a separate process per each user
            max_workers=config["query"]["users"]["count"]
        ) as executor:
            futures = [
                executor.submit(
                    run_query_user,
                    i,
                    pubkeys,
                    custom_endpoints,
                    config["query"],
                )
                for i in range(config["query"]["users"]["count"])
            ]
            print("Querying started. Press Ctrl+C to stop.")

            try:
                for future in futures:
                    future.result()  # Catch any exceptions from processes
            except KeyboardInterrupt:
                print("\nReceived Ctrl+C, shutting down...")
            except Exception as e:
                print(f"Process crashed: {e}")
            finally:
                print("\nCleaning up resources...")
                executor.shutdown(wait=False)


if __name__ == "__main__":
    run()
