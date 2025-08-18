import time
from typing import List
import requests
import re
import csv
import random


def fetch(url: str, endpoint: str) -> List[str]:
    url = f"{url}/{endpoint}s"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        pattern = rf'/page/{endpoint}/([^"\'>\s]*)'  # Take contents of each pubkey
        return re.findall(pattern, response.text)
    else:
        print(f"Error fetching URL {url}. Code: {response.status_code}")
        raise Exception(f"HTTP {response.status_code}: {response.reason}")


def run_query_user(user_id, pubkeys, custom_endpoints, query):
    user = QueryUser(user_id, pubkeys, custom_endpoints, query)
    user.start_querying()


class QueryUser:
    def __init__(
        self,
        user_id: int,
        pubkeys: List[str],
        custom_endpoints: dict[str, float],
        query: dict,
    ) -> None:
        self.user_id = user_id
        random.seed(query["seed"] + user_id)  # Every user gets a separate seed
        self.pubkeys = pubkeys
        self.path_to_logs = query["logging"]["log_path"]
        self.custom_endpoints = custom_endpoints
        self.timeout = query["timeout"]
        # 0 - count nanopubs for this repo
        # 1 - count statemements in all nanopubs for this repo
        # TODO: factor this out to config
        self.queries = [
            """prefix npa: <http://purl.org/nanopub/admin/>
                        select * where {
                            npa:thisRepo npa:hasNanopubCount ?count .
                        }""",
            """prefix np: <http://www.nanopub.org/nschema#>

                    select (count(*) as ?count) where {
                    ?nanopub a np:Nanopublication ;
                            np:hasAssertion ?assertion .
                    graph ?assertion {
                        ?subject ?predicate ?object .
                    }
                    }
            """,
        ]

    def _select_query(self) -> int:
        # TODO: implement query mix probabilities
        probs_q1 = 0.5  # Select a random query with equal probs
        rand = random.random()
        if rand < probs_q1:
            return 0
        else:
            return 1

    def _select_endpoint(self) -> str:
        rand = random.random()
        cumulative = 0.0

        for (
            endpoint,
            prob,
        ) in self.custom_endpoints.items():  # Check to which bracket the prob landed
            cumulative += prob
            if rand < cumulative:
                return endpoint

        return random.choice(self.pubkeys)

    def start_querying(self):
        with open(
            f"{self.path_to_logs}/log_{self.user_id}.csv",
            "a",
            newline="",
            buffering=1,
        ) as f:
            writer = csv.writer(f)
            if f.tell() == 0:  # Check if file is empty, then add header for clarity
                writer.writerow(  # Header for csv file
                    [
                        "query_id",
                        "status",
                        "n_lines_returned",
                        "query_result",
                        "response_elapsed_time",
                        "request_start_timestamp",
                        "request_end_timestamp",
                    ]
                )
            while True:
                endpoint = self._select_endpoint()
                row = self._run_sparql_query(endpoint, self._select_query())
                writer.writerow(
                    row
                )  # Buffering is set to 1, so no manual flushing needed

    def _run_sparql_query(self, endpoint_url, query_id):
        params = {"query": self.queries[query_id]}
        start_timestamp = time.time()
        response = requests.get(endpoint_url, params=params, timeout=self.timeout)
        end_timestamp = time.time()
        return (
            query_id,
            "ok"
            if 200 <= response.status_code < 300
            else (
                "timeout" if response.status_code in [408, 504] else "failed"
            ),  # 408 - request timeout, 504 - gateway timeout
            response.text.count("\n")
            - 1,  # Count number of rows returned from the query by counting caret returns - 1 (header)
            response.text.split("\r\n")[1],  # Actual count returned by the sparql
            response.elapsed.microseconds,
            start_timestamp,
            end_timestamp,
        )
