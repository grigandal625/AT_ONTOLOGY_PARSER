from dataclasses import dataclass
from typing import TYPE_CHECKING

from at_ontology_parser.base import Instance

if TYPE_CHECKING:
    from at_ontology_parser.ontology.instances.vertex import Vertex
    from at_ontology_parser.reference import OntologyReference
    from at_ontology_parser.model.types.relationship_type import RelationshipType


@dataclass(kw_only=True)
class Relationship(Instance):
    type: "OntologyReference[RelationshipType]"
    source: "OntologyReference[Vertex]"
    target: "OntologyReference[Vertex]"
