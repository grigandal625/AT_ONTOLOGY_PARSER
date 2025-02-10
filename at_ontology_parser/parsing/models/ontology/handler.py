from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.ontology.handler import Ontology
from at_ontology_parser.parsing.models.base import OntologyEntityModel
from at_ontology_parser.parsing.models.model.definitions.import_definition import Imports
from at_ontology_parser.parsing.models.ontology.instances.relationship import Relationships
from at_ontology_parser.parsing.models.ontology.instances.vertex import Vertices


class OntologyHandlerModel(OntologyEntityModel):
    name: str
    imports: Optional[Imports] = Field(default_factory=lambda: Imports([]))
    vertices: Optional[Vertices] = Field(default_factory=lambda: Vertices({}))
    relationships: Optional[Relationships] = Field(default_factory=lambda: Relationships({}))

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = Ontology(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: Ontology, context: Context):
        if result.imports:
            result.imports = self.imports.to_internal(
                context=context.create_child("imports", self.imports, result), owner=result
            )
        if result.vertices:
            result.vertices = self.vertices.to_internal(
                context=context.create_child("vertices", self.vertices, result), owner=result
            )
        if result.relationships:
            result.relationships = self.relationships.to_internal(
                context=context.create_child("relationships", self.relationships, result), owner=result
            )
        return super().insert_dependent_data(result, context)
