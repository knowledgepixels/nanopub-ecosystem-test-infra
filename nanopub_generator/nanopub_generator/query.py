import time
from typing import List
import requests
import re
import csv
from random import Random


def fetch(url: str, endpoint: str) -> List[str]:
    url = f"{url}/{endpoint}s"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        pattern = rf'/page/{endpoint}/([^"\'>\s]*)'  # Take contents of each pubkey
        return re.findall(pattern, response.text)
    else:
        print(f"Error fetching URL {url}. Code: {response.status_code}")
        raise Exception(f"HTTP {response.status_code}: {response.reason}")


def run_query_user(user_id, pubkeys, custom_endpoints, query, verbose: bool):
    user = QueryUser(user_id, pubkeys, custom_endpoints, query, verbose)
    user.start_querying()


class QueryUser:
    def __init__(
        self,
        user_id: int,
        pubkeys: List[str],
        custom_endpoints: dict[str, float],
        query: dict,
        verbose: bool,
    ) -> None:
        self.user_id = user_id
        # Every user gets a separate seed
        self.rng = Random(query["seed"] + user_id)
        self.pubkeys = pubkeys
        self.path_to_logs = query["logging"]["log_path"]
        self.custom_endpoints = custom_endpoints
        self.timeout = query["timeout"]
        self.queries = [q["query"] for q in query["queries"]]
        self.query_ids = list(range(len(self.queries)))  # List of query IDs
        self.query_weights = [q["weight"] for q in query["queries"]]
        self.verbose = verbose

    def _select_query(self) -> int:
        return self.rng.choices(
            population=self.query_ids,
            weights=self.query_weights,
            k=1,
        )[0]

    def _select_endpoint(self) -> str:
        rand = self.rng.random()
        cumulative = 0.0

        for (
            endpoint,
            prob,
        ) in self.custom_endpoints.items():  # Check to which bracket the prob landed
            cumulative += prob
            if rand < cumulative:
                return endpoint

        return self.rng.choice(self.pubkeys)

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

            BUFFER_SIZE = 20  # Buffer size for statistics
            row_buffer = []  # last 20 rows for statistics
            total_queries = 0
            with requests.Session() as session: # use individual session for each user
                while True:
                    endpoint = self._select_endpoint()
                    row = self._run_sparql_query(endpoint, self._select_query(), session)
                    row_buffer.append(row)
                    total_queries += 1
                    if len(row_buffer) >= BUFFER_SIZE:
                        query_times = [
                            r[4] for r in row_buffer
                            if r[1] == "ok"
                        ]
                        query_time = (sum(query_times) / 1e3) / len(query_times) if query_times else 0
                        row_buffer.clear()
                        print(
                            f"User {self.user_id:02}: "
                            f"Status: {row[1]}, "
                            f"Total queries: {total_queries}, "
                            f"Successful queries: {len(query_times)} / {BUFFER_SIZE}, "
                            f"Avg query time: {query_time:.2f} ms"
                        )
                    writer.writerow(
                        row
                    )  # Buffering is set to 1, so no manual flushing needed

    def _run_sparql_query(self, endpoint_url, query_id, session):
        params = {"query": self.queries[query_id]}
        start_timestamp = time.time()
        try:
            response = session.get(endpoint_url, params=params, timeout=self.timeout)
            end_timestamp = time.time()
            if self.verbose:
                print(
                    f"User {self.user_id:02}: Queried {endpoint_url} with query ID {query_id}. "
                    f"Status code: {response.status_code}, Time elapsed: {response.elapsed.total_seconds():.3f} s"
                )
        except requests.exceptions.ReadTimeout as e:
            end_timestamp = time.time()
            print(f"User {self.user_id:02}: Read timeout for query {query_id} on endpoint {endpoint_url}")
            return (query_id, "client_timeout", 0, "0", 0, start_timestamp, end_timestamp)
        rows = response.text.split("\r\n")
        value_returned = rows[1] if len(rows) > 1 else ""
        return (
            query_id,
            "ok"
            if 200 <= response.status_code < 300
            else (
                "server_timeout" if response.status_code in [408, 504] else "failed"
            ),  # 408 - request timeout, 504 - gateway timeout
            response.text.count("\n")
            - 1,  # Count number of rows returned from the query by counting caret returns - 1 (header)
            value_returned,  # Actual count returned by the sparql
            response.elapsed.microseconds,
            start_timestamp,
            end_timestamp,
        )
