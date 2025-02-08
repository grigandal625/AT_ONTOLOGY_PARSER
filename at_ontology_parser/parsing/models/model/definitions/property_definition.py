from typing import Any
from typing import Dict
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.definitions import PropertyDefinition
from at_ontology_parser.model.types import DataType
from at_ontology_parser.parsing.models.base import DefinitionModel
from at_ontology_parser.parsing.models.base import OntoRootModel
from at_ontology_parser.reference import OntologyReference


class PropertyDefinitionModel(DefinitionModel):
    type: Optional[str] = Field(default=None)
    required: Optional[bool] = Field(default=False)
    default: Optional[Any] = Field(default=None)
    allows_multiple: Optional[bool] = Field(default=True)
    min_assignments: Optional[int] = Field(default=None)
    max_assignments: Optional[int] = Field(default=None)

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = PropertyDefinition(**data)
        result.owner = owner
        return result

    def insert_dependent_data(self, result: PropertyDefinition, context: Context):
        if result.type:
            result.type = OntologyReference[DataType](
                alias=self.type,
                context=context.create_child(
                    "type",
                    self.type,
                    initiator=result,
                ),
            )
            result.type.owner = result
        return super().insert_dependent_data(result, context)


class Properties(OntoRootModel[Dict[str, PropertyDefinitionModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        return {
            key: prop.to_internal(context=context.create_child(key, data=prop), owner=owner, name=key)
            for key, prop in self.root.items()
        }
