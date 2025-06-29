import argparse
import httpx
import random
import schedule
import time
from typing import List

from nanopub import *
from data_gen import fake

parser = argparse.ArgumentParser(description="Nanopub generator")
parser.add_argument(
    "--registry-url",
    help="URL of the Registry endpoint for publishing nanopubs",
    required=True,
)
parser.add_argument(
    "--user-count",
    type=int,
    help="Number of users to generate (default: 10)",
    default=10,
)
parser.add_argument(
    "--post-interval",
    type=int,
    help="Interval in milliseconds between posts (default: 5000)",
    default=5000,
)

def publish_nanopub_safe(np_configs: List[NanopubConf]) -> None:
    try:
        publish_nanopub(np_configs)
    except Exception as e:
        print(f"Error publishing nanopub: {e}")


def publish_nanopub(np_configs: List[NanopubConf]) -> None:
    np_conf = random.choice(np_configs)
    pub = fake.np_about_paper(np_conf)
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
        for _ in range(args.user_count)
    ]
    # Schedule the nanopub publishing task
    schedule.every(args.post_interval / 1000).seconds.do(publish_nanopub_safe, np_configs=np_configs)

    print("Nanopub generator started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run()

