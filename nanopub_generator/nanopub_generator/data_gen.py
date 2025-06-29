from faker import Faker
import nanopub as np
import rdflib as rdf


CITO = rdf.Namespace("http://purl.org/spar/cito/")
TEMP = rdf.Namespace("http://purl.org/nanopub/temp/np#")
NPX = rdf.Namespace("http://purl.org/nanopub/x/")
TEST = rdf.Namespace("https://example.org/test/ontology/np#")


class NanopubFaker(Faker):
    """Custom provider to generate nanopub-related random data."""
    def orcid(self) -> str:
        """Generate a random ORCID ID."""
        # TODO: this does not cover all possible ORCID ranges and does not care about the checksum
        return (f"0000-000{self.random_int(1, 2)}-{self.random_int(0, 9999)}-"
                f"{self.random_int(0, 9999)}")

    def orcid_url(self) -> str:
        """Generate a random ORCID URL."""
        return f"https://orcid.org/{self.orcid()}"

    def np_profile(self) -> np.Profile:
        """Generate a random nanopub profile."""
        return np.Profile(
            orcid_id=self.orcid_url(),
            name=self.name(),
        )

    def np_about_paper(self, conf: np.NanopubConf) -> np.Nanopub:
        """Generate a nanopub about a paper."""
        a = rdf.Graph()
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
            TEST.PaperAssertion
        ))
        for i in range(self.random_int(1, 3)):
            a.add((
                TEMP.assertion,
                TEST.hasPaperColor,
                TEST["color" + self.color_name()]
            ))
        p = rdf.Graph()
        p.add((
            TEMP[''],
            NPX.hasNanopubType,
            TEST.PaperAssertion
        ))
        return np.Nanopub(
            conf=conf,
            assertion=a,
            pubinfo=p,
        )

fake = NanopubFaker()
