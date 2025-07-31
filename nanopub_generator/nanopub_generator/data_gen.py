from faker import Faker
import nanopub as np
from random import Random
import rdflib as rdf

from distribution import ParetoDistList, ParetoDist


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
        self.prefixes = ParetoDistList([
            self.iri_prefix()
            for _ in range(config['nanopubs']['prefix_count'])
        ], self.random)
        # Create nanopub types
        self.nanopub_types = ParetoDistList([
            self.iri_with_prefix(name_start='AboutPaper')
            for _ in range(config['nanopubs']['plain_assertion']['type_count'])
        ], self.random)
        # Helper distribution
        self.dist_0_20 = ParetoDist(self.random, 0, 20)

    def iri_prefix(self) -> str:
        """Generate a rng IRI prefix."""
        prefix = self.url() + self.uri_path()
        return prefix + '/' if self.random_int(0, 1) == 0 else prefix + '#'

    def iri_with_prefix(self, name_start: str = '') -> rdf.URIRef:
        """Generate a rng IRI with a prefix."""
        prefix = self.prefixes.sample_item()
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

    def add_blank_node(self, g: rdf.Graph) -> rdf.BNode:
        """Add a blank node with some extra information to the graph."""
        bnode = rdf.BNode()
        g.add((
            bnode,
            rdf.RDF.type,
            rdf.RDFS.Resource
        ))
        g.add((
            bnode,
            rdf.RDFS.label,
            rdf.Literal(self.word(part_of_speech='noun'), lang='en')
        ))
        for i in range(self.dist_0_20.sample()):
            g.add((
                bnode,
                TEST.relatedTo,
                self.iri_with_prefix(name_start='item')
            ))
        return bnode

    def np_about_paper(self, conf: np.NanopubConf) -> np.Nanopub:
        """Generate a nanopub about a paper."""
        a = rdf.Graph()
        np_type = self.nanopub_types.sample_item()
        a.add((
            TEMP.assertion,
            CITO.citesAsEvidence,
            rdf.URIRef(f"https://doi.org/{self.doi()}")
        ))
        match self.random_int(1, 3):
            case 1:
                # Langstring literal
                a.add((
                    TEMP.assertion,
                    rdf.RDFS.comment,
                    rdf.Literal(self.paragraph(nb_sentences=self.dist_0_20.sample() + 1), lang='en')
                ))
            case 2:
                # Integer literal
                a.add((
                    TEMP.assertion,
                    TEST.hasReviewScore,
                    rdf.Literal(self.random_int(1, 1000), datatype=rdf.XSD.integer)
                ))
            case 3:
                # Boolean literal
                a.add((
                    TEMP.assertion,
                    TEST.likesPaper,
                    rdf.Literal(self.random.choice(['true', 'false']), datatype=rdf.XSD.boolean)
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
        for i in range(self.dist_0_20.sample()):
            b_node = self.add_blank_node(a)
            a.add((
                TEMP.assertion,
                TEST.relatedTo,
                b_node
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