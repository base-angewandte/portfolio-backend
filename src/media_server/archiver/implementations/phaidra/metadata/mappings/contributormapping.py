import typing
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from core.models import Entry

from core.skosmos import get_json_data


@dataclass
class ConceptMapper:
    """Map an concept (uri) to others from skosmos."""

    '''Base uri, eg https://voc.uni-ak.ac.at/skosmos/povoc/en/page/advisor'''
    uri: str

    '''comparables, eg  {'http://vocab.getty.edu/aat/300160216', 'http://d-nb.info/gnd/4005565-6'}'''
    owl_sameAs: typing.Set[str]

    @classmethod
    def from_base_uri(cls, uri: str) -> 'ConceptMapper':
        graph = get_json_data(uri)['graph']
        for node in graph:
            if node['uri'] == uri:
                break
        else:
            raise RuntimeError('Got different data than expected ' + str(graph))

        if 'owl:sameAs' not in node:
            owl_sameAs = set()
        elif node['owl:sameAs'].__class__ is dict:
            owl_sameAs = set(node['owl:sameAs'].values())
        elif node['owl:sameAs'].__class__ is list:
            owl_sameAs = {element['uri'] for element in node['owl:sameAs']}
        else:
            raise RuntimeError(
                f'Can not handle node["owl:sameAs"] with type {node["owl:sameAs"].__class__} and value {node["owl:sameAs"]}'
            )
        return cls(
            uri=node['uri'],
            owl_sameAs=owl_sameAs,
        )

    def to_dict(self) -> dict:
        return {
            'uri': self.uri,
            'owl:sameAs': self.owl_sameAs,
        }


@dataclass
class BidirectionalConceptsMapper:
    concept_mappings: typing.Dict[str, ConceptMapper] = field(default_factory=dict)

    @classmethod
    def from_base_uris(cls, uris: typing.Set[str]) -> 'BidirectionalConceptsMapper':
        return cls(concept_mappings={uri: ConceptMapper.from_base_uri(uri) for uri in uris})

    def get_owl_sameAs_from_uri(self, uri: str) -> typing.Set[str]:
        return self.concept_mappings[uri].owl_sameAs

    def get_uris_from_owl_sameAs(self, owl_sameAs: str) -> typing.Set[str]:
        return {
            uri for uri, concept_mapper in self.concept_mappings.items() if owl_sameAs in concept_mapper.owl_sameAs
        }

    def add_uri(self, uri: str) -> 'BidirectionalConceptsMapper':
        if uri not in self.concept_mappings:
            self.concept_mappings[uri] = ConceptMapper.from_base_uri(uri)
        return self

    @classmethod
    def from_entry(cls, entry: 'Entry') -> 'BidirectionalConceptsMapper':
        if (entry.data is None) or ('contributors' not in entry.data):
            return cls.from_base_uris(set())
        contributors = entry.data['contributors']
        roles = {
            role['source']
            for contributor in contributors
            for role in contributor['roles']
            if 'roles' in contributor
            if 'source' in role
        }
        return cls.from_base_uris(roles)


def extract_phaidra_role_code(role_uri):
    """Returns the role "key" as used in Phaidra-JSON LD."""
    return f'role:{role_uri.split("/")[-1]}'
