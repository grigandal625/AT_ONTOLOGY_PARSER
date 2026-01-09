from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from at_ontology_parser.base import Instance

if TYPE_CHECKING:
    from at_ontology_parser.model.types.vertex_type import VertexType
    from at_ontology_parser.reference import OntologyReference


@dataclass(kw_only=True)
class Vertex(Instance):
    type: "OntologyReference[VertexType]" = field(repr=False)
