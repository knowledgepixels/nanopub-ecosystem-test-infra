from random import Random

from nanopub import *

from constants import *
from data_gen import NanopubFaker
from recent_nanopubs import RecentNanopubs


class NanopubGenerator:
    def __init__(self, config: dict, args):
        self.dry_run = args.dry_run
        self.config = config
        self.rng = Random(config['generator']['seed'])
        self.recent_nps = RecentNanopubs(config, self.rng)
        self.fake = NanopubFaker(config, self.rng, self.recent_nps)
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

    def choose_nanopub_type(self) -> str:
        """Choose a nanopub type based on the configured weights."""
        return self.rng.choices(
            population=NP_TYPES,
            weights=[
                self.config['nanopubs'][np_type]['weight']
                for np_type in NP_TYPES
            ],
            k=1
        )[0]

    def publish_nanopub_safe(self) -> None:
        try:
            self.publish_nanopub()
        except Exception as e:
            print(f"Error publishing nanopub: {e}")

    def publish_nanopub(self) -> None:
        # TODO: use ParetoDistList to sample the user
        np_conf = self.rng.choice(self.np_configs)
        np_type = self.choose_nanopub_type()
        if np_type == NP_TYPE_PLAIN:
            pub = self.fake.np_about_paper(np_conf)
        elif np_type == NP_TYPE_COMMENT:
            recent_pub = self.recent_nps.get_recent_nanopub()
            if recent_pub is None:
                print("No recent nanopub to comment on.")
                return
            pub = self.fake.np_comment(np_conf, recent_pub.source_uri)
        else:
            raise NotImplementedError(f"Unsupported nanopub type: {np_type}")

        pub.sign()
        self.recent_nps.update_recent_nanopubs(pub, NP_TYPE_PLAIN)
        if self.dry_run:
            print(f"\n---- Dry run: Would publish nanopub: ----\n")
            print(pub)
        else:
            pub.publish()
            print(f"Published nanopub: {pub.source_uri}")