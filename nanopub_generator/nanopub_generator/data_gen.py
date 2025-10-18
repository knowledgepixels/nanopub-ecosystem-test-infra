from faker import Faker
import nanopub as np
from random import Random
import rdflib as rdf

from distribution import ParetoDistList, ParetoDist
from recent_nanopubs import RecentNanopubs

CITO = rdf.Namespace("http://purl.org/spar/cito/")
TEMP = rdf.Namespace("http://purl.org/nanopub/temp/np#")
NPX = rdf.Namespace("http://purl.org/nanopub/x/")
TEST = rdf.Namespace("https://example.org/test/ontology/np#")


class NanopubFaker(Faker):
    """Custom provider to generate nanopub-related rng data."""
    def __init__(self, config: dict, rng: Random, recent_nps: RecentNanopubs):
        super().__init__()
        self.random = rng
        self.config = config
        self.recent_nps = recent_nps
        # Create prefixes
        self.prefixes = ParetoDistList([
            self.iri_prefix()
            for _ in range(self.config['nanopubs']['prefix_count'])
        ], self.random)
        # Create nanopub types
        self.nanopub_types = ParetoDistList([
            self.iri_with_prefix(name_start='AboutPaper')
            for _ in range(self.config['nanopubs']['plain_assertion']['type_count'])
        ], self.random)
        # Common IRIs
        self.common_iris = ParetoDistList([
            self.iri_with_prefix(name_start='common')
            for _ in range(self.config['nanopubs']['plain_assertion']['iris']['common_count'])
        ], self.random)
        self.common_iri_probability = self.config['nanopubs']['plain_assertion']['iris']['common_probability']
        self.recent_nanopub_iri_probability = self.config['nanopubs']['plain_assertion']['iris']['recent_nanopub_probability']
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

    def iri_with_commonality(self) -> rdf.URIRef:
        """Generate a rng IRI that may be common or recent."""
        r = self.random.random()
        if r < self.common_iri_probability:
            # Use a common IRI
            return self.common_iris.sample_item()
        elif r < self.common_iri_probability + self.recent_nanopub_iri_probability:
            # Use a recent nanopub IRI
            recent_np = self.recent_nps.get_recent_nanopub()
            if recent_np is not None:
                return rdf.URIRef(recent_np.source_uri)
        return self.iri_with_prefix('uncommon')

    def orcid(self) -> str:
        """Generate an rng ORCID ID."""
        # note: this does not cover all possible ORCID ranges and does not care about the checksum
        return (f"0000-000{self.random_int(1, 2)}-{self.random_int(0, 9999)}-"
                f"{self.random_int(0, 9999)}")

    def orcid_url(self) -> str:
        """Generate an rng ORCID URL."""
        return f"https://orcid.org/{self.orcid()}"

    def np_profile(self, orcid_id: str = None, name: str = None) -> np.Profile:
        """Generate an rng nanopub profile."""
        return np.Profile(
            orcid_id=self.orcid_url() if orcid_id is None else orcid_id,
            name=self.name() if name is None else name,
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
                self.iri_with_commonality()
            ))
        return bnode

    def np_about_paper(self, conf: np.NanopubConf) -> np.Nanopub:
        """Generate a nanopub about a paper."""
        np_type = self.nanopub_types.sample_item()
        a = self.np_plain_assertion(np_type)
        return self.np_base(a, conf, np_type)

    def np_plain_assertion(self, np_type: rdf.URIRef) -> rdf.Graph:
        a = rdf.Graph()
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
        return a

    def np_comment(self, conf: np.NanopubConf, about_iri: str) -> np.Nanopub:
        """Generate a nanopub commenting a different nanopub or any other IRI."""
        a = rdf.Graph()
        a.add((
            rdf.URIRef(about_iri),
            rdf.RDFS.comment,
            rdf.Literal(self.paragraph(nb_sentences=3), lang='en')
        ))
        return self.np_base(a, conf, TEST.Comment)
        
    def np_retract(self, conf: np.NanopubConf, to_retract: np.Nanopub) -> np.Nanopub:
        """Create a retraction for a given nanopub."""
        a = rdf.Graph()
        a.add(
            (
                rdf.URIRef(conf.profile.orcid_id),
                NPX.retracts,
                rdf.URIRef(to_retract.source_uri),
            )
        )
        return self.np_base(a, conf, NPX.retracts)

    def np_update(self, conf: np.NanopubConf, supersede: np.Nanopub) -> np.Nanopub:
        """Generate a nanopub updating a different nanopub or any other IRI."""
        if self.random.random() < self.config['nanopubs']['update_assertion']['reuse_type_probability']:
            # Reuse the type of the original nanopub
            np_type = list(supersede.pubinfo.subject_objects(NPX.hasNanopubType))[0][1]
        else:
            # Use a random type
            np_type = self.nanopub_types.sample_item()
        a = self.np_plain_assertion(np_type)
        pub = self.np_base(a, conf, np_type)
        pub.pubinfo.add((
            TEMP[''],
            NPX.supersedes,
            rdf.URIRef(supersede.source_uri)
        ))
        return pub
