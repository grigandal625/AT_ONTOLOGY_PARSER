from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.handler import OntologyModel
from at_ontology_parser.parsing.models.base import OntologyEntityModel
from at_ontology_parser.parsing.models.model.types.data_type import DataTypes
from at_ontology_parser.parsing.models.model.types.relationship_type import RelationshipTypes
from at_ontology_parser.parsing.models.model.types.vertex_type import VertexTypes


class OntologyModelModel(OntologyEntityModel):
    name: str
    data_types: Optional[DataTypes] = Field(default_factory=lambda: DataTypes({}))
    vertex_types: Optional[VertexTypes] = Field(default_factory=lambda: VertexTypes({}))
    relationship_types: Optional[RelationshipTypes] = Field(default_factory=lambda: RelationshipTypes({}))

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = OntologyModel(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: OntologyModel, context: Context):
        if result.data_types:
            result.data_types = self.data_types.to_internal(
                context=context.create_child("data_types", self.data_types, result), owner=result
            )
        if result.vertex_types:
            result.vertex_types = self.vertex_types.to_internal(
                context=context.create_child("vertex_types", self.vertex_types, result), owner=result
            )
        if result.relationship_types:
            result.relationship_types = self.relationship_types.to_internal(
                context=context.create_child("relationship_types", self.relationship_types, result), owner=result
            )
        return super().insert_dependent_data(result, context)
