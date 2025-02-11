from typing import Any
from typing import Dict
from typing import Optional

from jsonschema.exceptions import SchemaError
from jsonschema.validators import Draft7Validator
from pydantic import Field
from pydantic import model_validator

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import DataType
from at_ontology_parser.parsing.models.base import DerivableModel
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.model.definitions.constraint_definition import Constraints
from at_ontology_parser.reference import OntologyReference


class DataTypeModel(DerivableModel):
    constraints: Optional[Constraints] = Field(default_factory=lambda: Constraints([]))
    object_schema: Optional[Dict[str, Any] | str] = Field(default=None)

    @model_validator(mode="before")
    def validate_object_schema(cls, values: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if values.get("object_schema"):
            if isinstance(values.get("object_schema"), str) and values.get("object_schema").startswith("$"):
                return values
            try:
                Draft7Validator.check_schema(values["object_schema"])
            except SchemaError as e:
                raise ValueError(f"Invalid object_schema: {e}")
        return values

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase) -> DataType:
        result = DataType(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: DataType, context: Context) -> DataType:
        if result.derived_from:
            result.derived_from = OntologyReference[DataType](
                alias=self.derived_from, context=context.create_child("derived_from", self.derived_from, result)
            )
            result.derived_from.owner = result
        if result.constraints:
            result.constraints = self.constraints.to_internal(
                context=context.create_child("constraints", self.constraints, result), owner=result
            )
        return super().insert_dependent_data(result, context)


class DataTypes(OntoRootModel[Dict[str, DataTypeModel]]):
    def to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, DataType]:
        return super().to_internal(context=context, owner=owner, **kwargs)

    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, DataType]:
        return {
            key: data_type.to_internal(context=context.create_child(key, data_type), owner=owner, name=key)
            for key, data_type in self.root.items()
        }
