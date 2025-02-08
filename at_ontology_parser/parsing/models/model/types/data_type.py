from typing import Any
from typing import Dict
from typing import Optional

from jsonschema.validators import Draft7Validator
from pydantic import Field
from pydantic import model_validator

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.types import DataType
from at_ontology_parser.parsing.models.base import DerivableModel
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.parsing.models.model.definitions.constraint_definition import Constraints


class DataTypeModel(DerivableModel):
    constraints: Optional[Constraints] = Field(default_factory=lambda: Constraints([]))
    object_schema: Optional[Dict[str, Any]] = Field(default=None)

    @model_validator(pre=True)
    def validate_object_schema(cls, values: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if values.get("object_schema"):
            validator = Draft7Validator(values["object_schema"])
            errors = list(validator.iter_errors(values["object_schema"]))
            if errors:
                raise ValueError(f"Invalid object schema: {errors}")
        return values

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase) -> DataType:
        result = DataType(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: DataType, context: Context) -> DataType:
        if result.constraints:
            result.constraints = self.constraints.to_internal(
                context=context.create_child("constraints", self.constraints, result), owner=result
            )
        return super().insert_dependent_data(result, context)


class DataTypes(OntoRootModel[Dict[str, DataTypeModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs) -> Dict[str, DataType]:
        return {
            key: data_type.to_internal(context=context.create_child(key, data_type), owner=owner, name=key)
            for key, data_type in self.root.items()
        }
