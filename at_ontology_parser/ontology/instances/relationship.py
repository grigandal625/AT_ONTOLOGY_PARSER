from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from at_ontology_parser.base import Instance

if TYPE_CHECKING:
    from at_ontology_parser.ontology.instances.vertex import Vertex
    from at_ontology_parser.reference import OntologyReference
    from at_ontology_parser.model.types.relationship_type import RelationshipType


@dataclass(kw_only=True)
class Relationship(Instance):
    type: "OntologyReference[RelationshipType]" = field(repr=False)
    source: "OntologyReference[Vertex]" = field(repr=False)
    target: "OntologyReference[Vertex]" = field(repr=False)
