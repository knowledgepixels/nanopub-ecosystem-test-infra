import argparse
import httpx
import random
import schedule
import time
from typing import List
import yaml

from nanopub import *
from data_gen import fake

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

def publish_nanopub_safe(np_configs: List[NanopubConf], config: dict, dry_run: bool) -> None:
    try:
        publish_nanopub(np_configs, config, dry_run)
    except Exception as e:
        print(f"Error publishing nanopub: {e}")


def publish_nanopub(np_configs: List[NanopubConf], config: dict, dry_run: bool) -> None:
    np_conf = random.choice(np_configs)
    pub = fake.np_about_paper(np_conf)
    if dry_run:
        print(f"\n---- Dry run: Would publish nanopub: ----\n")
        print(pub)
    else:
        pub.publish()
        print(f"Published nanopub: {pub.source_uri}")


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
    # Create users
    np_configs = [
        NanopubConf(
            use_server=args.registry_url,
            profile=fake.np_profile(),
            add_prov_generated_time=True,
            add_pubinfo_generated_time=True,
            attribute_publication_to_profile=True,
            attribute_assertion_to_profile=True,
        )
        for _ in range(config['users']['count'])
    ]
    # Schedule the nanopub publishing task
    schedule.every(config['generator']['post_interval'] / 1000).seconds.do(
        publish_nanopub_safe,
        np_configs=np_configs,
        config=config,
        dry_run=args.dry_run,
    )

    print("Nanopub generator started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run()

