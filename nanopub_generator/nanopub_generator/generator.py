from random import Random

from nanopub import *

from data_gen import NanopubFaker
from distribution import ParetoDist

class NanopubGenerator:
    def __init__(self, config: dict, args):
        self.dry_run = args.dry_run
        self.config = config
        self.rng = Random(config['generator']['seed'])
        self.fake = NanopubFaker(config, self.rng)
        # Create users
        self.np_configs = [
            NanopubConf(
                use_server=args.registry_url,
                profile=self.fake.np_profile(),
                add_prov_generated_time=True,
                add_pubinfo_generated_time=True,
                attribute_publication_to_profile=True,
                attribute_assertion_to_profile=True,
            )
            for _ in range(config['users']['count'])
        ]
        # Create prefixes
        self.prefixes = ParetoDist([
            self.fake.iri_prefix()
            for _ in range(config['nanopubs']['prefix_count'])
        ], self.rng)
        # Create nanopub types
        self.nanopub_types = ParetoDist([
            self.fake.iri_with_prefix(self.prefixes, name_start='Type')
            for _ in range(config['nanopubs']['plain_assertion']['type_count'])
        ], self.rng)

    def publish_nanopub_safe(self) -> None:
        try:
            self.publish_nanopub()
        except Exception as e:
            print(f"Error publishing nanopub: {e}")

    def publish_nanopub(self) -> None:
        np_conf = self.rng.choice(self.np_configs)
        pub = self.fake.np_about_paper(np_conf)
        if self.dry_run:
            print(f"\n---- Dry run: Would publish nanopub: ----\n")
            print(pub)
        else:
            pub.publish()
            print(f"Published nanopub: {pub.source_uri}")