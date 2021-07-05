from __future__ import annotations

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
    owl_sameAs: set[str]

    @classmethod
    def from_base_uri(cls, uri: str) -> ConceptMapper:
        graph = get_json_data(uri)['graph']
        for node in graph:
            if node['uri'] == uri:
                break
        else:
            raise RuntimeError('Got different data than expected ' + str(graph))

        return cls(uri=node['uri'], owl_sameAs={element['uri'] for element in node['owl:sameAs']})

    def to_dict(self) -> dict:
        return {
            'uri': self.uri,
            'owl:sameAs': self.owl_sameAs,
        }


@dataclass
class BidirectionalConceptsMapper:
    concept_mappings: dict[str, ConceptMapper] = field(default_factory=dict)

    @classmethod
    def from_base_uris(cls, uris: set[str]) -> BidirectionalConceptsMapper:
        return cls(concept_mappings={uri: ConceptMapper.from_base_uri(uri) for uri in uris})

    def get_owl_sameAs_from_uri(self, uri: str) -> set[str]:
        return self.concept_mappings[uri].owl_sameAs

    def get_uris_from_owl_sameAs(self, owl_sameAs: str) -> set[str]:
        return {
            uri for uri, concept_mapper in self.concept_mappings.items() if owl_sameAs in concept_mapper.owl_sameAs
        }

    def add_uri(self, uri: str) -> BidirectionalConceptsMapper:
        if uri not in self.concept_mappings:
            self.concept_mappings[uri] = ConceptMapper.from_base_uri(uri)
        return self

    @classmethod
    def from_entry(cls, entry: 'Entry') -> BidirectionalConceptsMapper:
        if 'contributors' not in entry.data:
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
