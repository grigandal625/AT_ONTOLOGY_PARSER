from enum import Enum

from at_ontology_parser.model.types.data_type import DataType
from at_ontology_parser.model.types.relationship_type import RelationshipType
from at_ontology_parser.model.types.vertex_type import VertexType


class ONTOLOGY_TYPES(Enum):
    data_types = DataType
    vertex_types = VertexType
    relationship_types = RelationshipType

    @classmethod
    def class_mapping(cls):
        return {v.value.__name__: v.value for v in cls}

    @classmethod
    def sections(cls):
        return {v.name: v.value for v in cls}

    @classmethod
    def all(cls):
        return [v.value for v in cls]

    @classmethod
    def class_to_section_mapping(cls):
        return {v.value: v.name for v in cls}


__all__ = [
    "DataType",
    "VertexType",
    "RelationshipType",
    "ONTOLOGY_TYPES",
]
