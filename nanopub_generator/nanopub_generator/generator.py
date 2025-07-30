from random import Random

from nanopub import *

from data_gen import NanopubFaker
from distribution import ParetoDistList

NP_TYPE_PLAIN = 'plain_assertion'
NP_TYPE_COMMENT = 'comment'

NP_TYPES = [
    NP_TYPE_PLAIN,
    NP_TYPE_COMMENT,
]

class NanopubGenerator:
    def __init__(self, config: dict, args):
        self.dry_run = args.dry_run
        self.config = config
        self.rng = Random(config['generator']['seed'])
        self.fake = NanopubFaker(config, self.rng)
        self.recent_nanopubs = {k: [] for k in NP_TYPES}
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

    def update_recent_nanopubs(self, nanopub: Nanopub, np_type: str) -> None:
        """Update the list of recent nanopubs."""
        np_list = self.recent_nanopubs[np_type]
        np_list.append(nanopub)
        if len(np_list) > self.config['nanopubs'][np_type]['recent_count']:
            np_list.pop(self.rng.randint(0, len(np_list)))

    def get_recent_nanopub(self, np_type: str = None) -> Nanopub | None:
        """Get a recent nanopub of the specified type or None if there are no recent nanopubs."""
        if np_type is None:
            lists = list(self.recent_nanopubs.values())
            self.rng.shuffle(lists)
        else:
            lists = [self.recent_nanopubs[np_type]]
        for np_list in lists:
            if len(np_list) > 0:
                return self.rng.choice(np_list)
        return None

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
            recent_pub = self.get_recent_nanopub()
            if recent_pub is None:
                print("No recent nanopub to comment on.")
                return
            pub = self.fake.np_comment(np_conf, recent_pub.source_uri)
        else:
            raise NotImplementedError(f"Unsupported nanopub type: {np_type}")

        pub.sign()
        self.update_recent_nanopubs(pub, NP_TYPE_PLAIN)
        if self.dry_run:
            print(f"\n---- Dry run: Would publish nanopub: ----\n")
            print(pub)
        else:
            pub.publish()
            print(f"Published nanopub: {pub.source_uri}")