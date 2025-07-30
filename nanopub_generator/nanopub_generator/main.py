import argparse
import httpx
import schedule
import time
import yaml

from generator import NanopubGenerator

parser = argparse.ArgumentParser(description="Nanopub generator")
parser.add_argument(
    "--registry-url",
    help="URL of the Registry endpoint for publishing nanopubs",
    required=True,
)
parser.add_argument(
    "--dry-run",
    action='store_true',
    help="If set, do not actually publish nanopubs, just print what would be published",
)
parser.add_argument(
    "--config-file",
    type=str,
    help="Path to a configuration file (config.yaml) for the generator. Default: ./config.yaml",
    default="./config.yaml",
)

def verify_test_instance(url: str) -> None:
    """Verify that the provided URL points a test instance of the Nanopub Registry."""
    print(f"Verifying that {url} is a test instance of the Nanopub Registry...")
    r = httpx.get(url)
    assert r.status_code == 200, f"Failed to connect to {url}, status code: {r.status_code}"
    assert 'Nanopub-Registry-Test-Instance' in r.headers, f"{url} is not a Nanopub Registry"
    assert r.headers['Nanopub-Registry-Test-Instance'] == 'true', f"{url} is not a test instance of the Nanopub Registry"


def run():
    args = parser.parse_args()
    try:
        with open(args.config_file, 'rt') as f:
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

    if not args.dry_run:
        # Verify the registry URL
        try:
            verify_test_instance(args.registry_url)
        except Exception as e:
            print(f"Error verifying registry URL: {e}")
            return 1

    generator = NanopubGenerator(config, args)
    # Schedule the nanopub publishing task
    schedule.every(config['generator']['post_interval'] / 1000).seconds.do(
        generator.publish_nanopub_safe,
    )

    print("Nanopub generator started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run()

