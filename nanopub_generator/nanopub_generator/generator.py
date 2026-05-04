from collections import deque
import itertools
import copy
from random import Random

from nanopub import *

from constants import *
from data_gen import NanopubFaker
from recent_nanopubs import RecentNanopubs
from distribution import ParetoDistList, ParetoDist
import rdflib as rdf

class NanopubGenerator:
    def __init__(self, config: dict, args):
        self.dry_run = args.dry_run
        self.config = config
        self.rng = Random(config["generator"]["seed"])
        self.counter_nanopubs = 0
        self.registry_urls = [item.strip() for item in args.registry_urls.split(',')]
        self.recent_nps_list = [RecentNanopubs(config, self.rng) for registry in self.registry_urls]
        self.faker_list = [NanopubFaker(config, self.rng, self.recent_nps_list[registry]) for registry in range(len(self.registry_urls))]
        self.range_registries = range(len(self.registry_urls))
        self.schedule = itertools.cycle(self.range_registries) # publish to registries in cycle
        type_count = config["nanopubs"]["plain_assertion"]["type_count"]
        overlap_per_registry = round(type_count/len(self.registry_urls))
        if len(self.registry_urls) > 1:
            for registry_num in range(len(self.registry_urls)):
                self.faker_list[registry_num].nanopub_types = ParetoDistList([
                    rdf.URIRef(f"https://example.org/types#{np_type%type_count}") # take mod so to not overflow the total type count
                    for np_type in range(registry_num*overlap_per_registry, (registry_num*overlap_per_registry+overlap_per_registry*2))
                ], self.rng)
               
        # Create users
        self.pareto_pubkeys = ParetoDist(self.rng, 1, 50, 5.5)
        self.np_accounts_map = {
            profile.orcid_id: deque(
                [
                    NanopubConf(
                        use_server= self.registry_urls[0] if len(self.registry_urls) == 1 else None,
                        profile=profile,
                        add_prov_generated_time=False,
                        add_pubinfo_generated_time=False,
                        attribute_publication_to_profile=True,
                        attribute_assertion_to_profile=True,
                    )
                ],
                maxlen=self.pareto_pubkeys.sample(),
            )
            for _ in range(config["generator"]["users"]["count"])
            for profile in [self.faker_list[0].np_profile()] # generate profiles from one NanopubFaker regardless of registries
        }
        self.update_accounts_details()
        self.accounts_to_complete = [
            k for k, v in self.np_accounts_map.items() if len(v) < v.maxlen
        ]

    def update_accounts_details(self):
        self.np_accounts_list = ParetoDistList(
            list(self.np_accounts_map.values()),
            self.rng,
            1,
        )
        self.rev_np_accounts_list = ParetoDistList(
            list(self.np_accounts_map.keys())[::-1],
            self.rng,
            1,
        )

    def choose_nanopub_type(self) -> str:
        """Choose a nanopub type based on the configured weights."""
        return self.rng.choices(
            population=NP_TYPES,
            weights=[
                self.config["nanopubs"][np_type]["weight"] for np_type in NP_TYPES
            ],
            k=1,
        )[0]

    def publish_nanopub_safe(self) -> None:
        try:
            self.publish_nanopub()
        except Exception as e:
            print(f"Error publishing nanopub: {e}")

    def add_pubkey(self):
        if (len(self.accounts_to_complete)) > 0:
            account_orcid = self.rng.choice(self.accounts_to_complete)
            self.np_accounts_map[account_orcid].append(
                NanopubConf(
                    use_server=self.registry_urls[0] if len(self.registry_urls) == 1 else None,
                    profile=self.faker_list[0].np_profile( # generate profiles from one NanopubFaker regardless of registries
                        account_orcid,
                        self.np_accounts_map[account_orcid][0].profile.name,
                    ),
                    add_prov_generated_time=False,
                    add_pubinfo_generated_time=False,
                    attribute_publication_to_profile=True,
                    attribute_assertion_to_profile=True,
                )
            )
            # If the account's profiles are filled, remove it from the list
            if (
                len(self.np_accounts_map[account_orcid])
                == self.np_accounts_map[account_orcid].maxlen
            ):
                self.accounts_to_complete.remove(account_orcid)
        else:
            print("No accounts to add pubkeys to.")

    def remove_account(self):
        account_to_remove = self.rev_np_accounts_list.sample_item()
        self.np_accounts_map.pop(account_to_remove)
        if account_to_remove in self.accounts_to_complete:
            self.accounts_to_complete.remove(account_to_remove)
        self.update_accounts_details()

    def add_account(self):
        profile = self.faker_list[0].np_profile() # generate profiles from one NanopubFaker regardless of registries
        account = deque(
            [
                NanopubConf(
                    use_server=self.registry_urls[0] if len(self.registry_urls) == 1 else None,
                    profile=profile,
                    add_prov_generated_time=False,
                    add_pubinfo_generated_time=False,
                    attribute_publication_to_profile=True,
                    attribute_assertion_to_profile=True,
                )
            ],
            maxlen=self.pareto_pubkeys.sample(),
        )
        self.np_accounts_map.update({profile.orcid_id: account})
        self.update_accounts_details()
        if account.maxlen > 1:
            self.accounts_to_complete.append(profile.orcid_id)

    def find_nanopub_posting_config(self, np_to_examine: nanopub.Nanopub):
        posting_account = self.np_accounts_map.get(np_to_examine.profile.orcid_id)
        if posting_account is None:
            raise Exception(
                "Posting account for nanopub was not found in the list of active accounts."
            )
        return np_to_examine.conf

    def publish_nanopub(self) -> None:
        np_account = self.np_accounts_list.sample_item()
        np_type = self.choose_nanopub_type()
        registry = next(self.schedule)# self.rng.choice(self.range_registries) choose next registry, can also be random
        print(f"Selected registry: {registry}: {self.registry_urls[registry]}")
        faker = self.faker_list[registry] # choose appropriate NanopubFaker
        recent_nps = self.recent_nps_list[registry] # recent nanopubs also depend on registry
        if len(np_account) == 1:
            np_config = copy.copy(np_account[0])
        else:
            select_pubkey = ParetoDist(self.rng, 0, len(np_account) - 1, 1)
            np_config = copy.copy(np_account[select_pubkey.sample()])
        np_config.use_server = self.registry_urls[registry] # modify profile to use selected registry, config is stored within np, so it is reused for updates/retractions
        if np_type == NP_TYPE_PLAIN:
            pub = faker.np_about_paper(np_config)
        elif np_type == NP_TYPE_COMMENT:
            recent_pub = recent_nps.get_recent_nanopub()
            if recent_pub is None:
                print("No recent nanopub to comment on.")
                return
            pub = faker.np_comment(np_config, recent_pub.source_uri)
        elif np_type == NP_TYPE_UPDATE:
            recent_pub = recent_nps.get_recent_nanopub(NP_TYPE_PLAIN)
            if recent_pub is None:
                print("No recent plain nanopub to update.")
                return
            poster_config = self.find_nanopub_posting_config(recent_pub)
            pub = faker.np_update(poster_config, recent_pub)
        elif np_type == NP_TYPE_RETRACT:
            # Retract random np (but not another retraction)
            nt_type_to_retract = self.rng.choice(
                [NP_TYPE_PLAIN, NP_TYPE_UPDATE, NP_TYPE_COMMENT]
            )
            recent_pub = recent_nps.get_recent_nanopub(nt_type_to_retract)
            if recent_pub is None:
                print(
                    f"Failed to find a recent publication of type {nt_type_to_retract} to retract"
                )
                return
            # Find the original configuration for the recent nanopub to reuse
            poster_config = self.find_nanopub_posting_config(recent_pub)
            pub = faker.np_retract(poster_config, recent_pub)
            recent_nps.remove_retracted(recent_pub)
        else:
            raise NotImplementedError(f"Unsupported nanopub type: {np_type}")

        pub.sign()
        recent_nps.update_recent_nanopubs(pub, np_type)
        if self.dry_run:
            print("\n---- Dry run: Would publish nanopub: ----\n")
            print(pub)
        else:
            pub.publish()
            print(f"Published nanopub: {pub.source_uri}")
        self.counter_nanopubs += 1
        if self.counter_nanopubs % 100 == 0:
            print("Adding a pubkey...")
            self.add_pubkey()
        if self.counter_nanopubs % 1000 == 0:
            print("Removing an old and adding a new account...")
            self.remove_account()
            self.add_account()
