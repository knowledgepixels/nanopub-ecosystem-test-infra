from faker import Faker
import nanopub as np
from random import Random
import rdflib as rdf

from distribution import ParetoDist


CITO = rdf.Namespace("http://purl.org/spar/cito/")
TEMP = rdf.Namespace("http://purl.org/nanopub/temp/np#")
NPX = rdf.Namespace("http://purl.org/nanopub/x/")
TEST = rdf.Namespace("https://example.org/test/ontology/np#")


class NanopubFaker(Faker):
    """Custom provider to generate nanopub-related rng data."""
    def __init__(self, config: dict, rng: Random):
        super().__init__()
        self.random = rng
        self.config = config
        # Create prefixes
        self.prefixes = ParetoDist([
            self.iri_prefix()
            for _ in range(config['nanopubs']['prefix_count'])
        ], self.random)
        # Create nanopub types
        self.nanopub_types = ParetoDist([
            self.iri_with_prefix(name_start='AboutPaper')
            for _ in range(config['nanopubs']['plain_assertion']['type_count'])
        ], self.random)

    def iri_prefix(self) -> str:
        """Generate a rng IRI prefix."""
        prefix = self.url() + self.uri_path()
        return prefix + '/' if self.random_int(0, 1) == 0 else prefix + '#'

    def iri_with_prefix(self, name_start: str = '') -> rdf.URIRef:
        """Generate a rng IRI with a prefix."""
        prefix = self.prefixes.sample()
        name_end = self.word(part_of_speech='noun')
        return rdf.URIRef(f"{prefix}{name_start}{name_end.capitalize()}")

    def orcid(self) -> str:
        """Generate a rng ORCID ID."""
        # note: this does not cover all possible ORCID ranges and does not care about the checksum
        return (f"0000-000{self.random_int(1, 2)}-{self.random_int(0, 9999)}-"
                f"{self.random_int(0, 9999)}")

    def orcid_url(self) -> str:
        """Generate a rng ORCID URL."""
        return f"https://orcid.org/{self.orcid()}"

    def np_profile(self) -> np.Profile:
        """Generate a rng nanopub profile."""
        return np.Profile(
            orcid_id=self.orcid_url(),
            name=self.name(),
        )

    def np_base(self, assertion: rdf.Graph, conf: np.NanopubConf, np_type: rdf.URIRef) -> np.Nanopub:
        p = rdf.Graph()
        p.add((
            TEMP[''],
            NPX.hasNanopubType,
            np_type
        ))
        return np.Nanopub(
            conf=conf,
            assertion=assertion,
            pubinfo=p,
        )

    def np_about_paper(self, conf: np.NanopubConf) -> np.Nanopub:
        """Generate a nanopub about a paper."""
        a = rdf.Graph()
        np_type = self.nanopub_types.sample()
        a.add((
            TEMP.assertion,
            CITO.citesAsEvidence,
            rdf.URIRef(f"https://doi.org/{self.doi()}")
        ))
        a.add((
            TEMP.assertion,
            rdf.RDFS.comment,
            rdf.Literal(self.paragraph(nb_sentences=3), lang='en')
        ))
        a.add((
            TEMP.assertion,
            rdf.RDF.type,
            np_type
        ))
        for i in range(self.random_int(1, 3)):
            a.add((
                TEMP.assertion,
                TEST.hasPaperColor,
                TEST["color" + self.color_name()]
            ))
        return self.np_base(a, conf, np_type)

    def np_comment(self, conf: np.NanopubConf, about_iri: str) -> np.Nanopub:
        """Generate a nanopub commenting a different nanopub or any other IRI."""
        a = rdf.Graph()
        a.add((
            rdf.URIRef(about_iri),
            rdf.RDFS.comment,
            rdf.Literal(self.paragraph(nb_sentences=3), lang='en')
        ))
        return self.np_base(a, conf, TEST.Comment)