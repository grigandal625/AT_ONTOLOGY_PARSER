from enum import Enum

from at_ontology_parser.ontology.instances.relationship import Relationship
from at_ontology_parser.ontology.instances.vertex import Vertex


class ONTOLOGY_INSTANCES(Enum):
    vertices = Vertex
    relationships = Relationship

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
    "Vertex",
    "Relationship",
    "ONTOLOGY_INSTANCES",
]
