from random import Random

from nanopub import *

from constants import *

class RecentNanopubs:
    def __init__(self, config: dict, rng: Random):
        self.config = config
        self.rng = rng
        self.recent_nanopubs = {k: [] for k in NP_TYPES}

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
