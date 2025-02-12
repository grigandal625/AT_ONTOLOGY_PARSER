import re
from typing import Any
from typing import Dict
from typing import Optional

from jsonschema import Draft7Validator
from jsonschema import SchemaError
from pydantic import Field
from pydantic import model_validator

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import LoadException
from at_ontology_parser.model.handler import OntologyModel
from at_ontology_parser.parsing.models.base import OntologyEntityModel
from at_ontology_parser.parsing.models.model.definitions.import_definition import Imports
from at_ontology_parser.parsing.models.model.types.data_type import DataTypes
from at_ontology_parser.parsing.models.model.types.relationship_type import RelationshipTypes
from at_ontology_parser.parsing.models.model.types.vertex_type import VertexTypes


class OntologyModelModel(OntologyEntityModel):
    name: str
    imports: Optional[Imports] = Field(default_factory=lambda: Imports([]))
    data_types: Optional[DataTypes] = Field(default_factory=lambda: DataTypes({}))
    vertex_types: Optional[VertexTypes] = Field(default_factory=lambda: VertexTypes({}))
    relationship_types: Optional[RelationshipTypes] = Field(default_factory=lambda: RelationshipTypes({}))
    schema_definitions: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="before")
    def validate_schema(cls, values: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if values.get("schema_definitions"):
            for key, value in values.get("schema_definitions").items():
                if not key.startswith("$") and not re.match(r"\w+", key[1:]):
                    raise ValueError(f"Invalid schema key: {key}")
                try:
                    Draft7Validator.check_schema(value)
                except SchemaError as e:
                    raise ValueError(f"Invalid schema value for key {key}: {e}")
        return values

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = OntologyModel(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: OntologyModel, context: Context):
        if result.imports:
            result.imports = self.imports.to_internal(
                context=context.create_child("imports", self.imports, result),
                owner=result,
            )
        if result.data_types:
            result.data_types = self.data_types.to_internal(
                context=context.create_child("data_types", self.data_types, result), owner=result
            )
            for data_type in result.data_types.values():
                if isinstance(data_type.object_schema, str):
                    if data_type.object_schema not in result.schema_definitions:
                        raise LoadException(
                            "Failed to load ontology model",
                            errors=[f'Invalid schema reference "{data_type.object_schema}"'],
                            context=context.create_child("data_types", result, result)
                            .create_child(data_type.name, data_type, data_type)
                            .create_child("object_schema", data_type.object_schema),
                        )
                    data_type.object_schema_resolved = result.schema_definitions[data_type.object_schema]
                else:
                    data_type.object_schema_resolved = data_type.object_schema
        if result.vertex_types:
            result.vertex_types = self.vertex_types.to_internal(
                context=context.create_child("vertex_types", self.vertex_types, result), owner=result
            )
        if result.relationship_types:
            result.relationship_types = self.relationship_types.to_internal(
                context=context.create_child("relationship_types", self.relationship_types, result), owner=result
            )
        return super().insert_dependent_data(result, context)
