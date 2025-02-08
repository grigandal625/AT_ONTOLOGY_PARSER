from typing import Optional

from pydantic import Field

from at_ontology_parser.base import Instancable
from at_ontology_parser.exceptions import Context
from at_ontology_parser.parsing.models.base import DerivableModel
from at_ontology_parser.parsing.models.model.definitions.artifact_definition import Artifacts
from at_ontology_parser.parsing.models.model.definitions.property_definition import Properties


class InstancableModel(DerivableModel):
    properties: Optional[Properties] = Field(default_factory=Properties({}))
    artifacts: Optional[Artifacts] = Field(default_factory=Artifacts({}))

    def insert_dependent_data(self, result: Instancable, context: Context):
        if result.properties:
            result.properties = self.properties.to_internal(
                context=context.create_child("properties", self.properties, result), owner=result
            )
        if result.artifacts:
            result.artifacts = self.artifacts.to_internal(
                context=context.create_child("artifacts", self.artifacts, result), owner=result
            )
        return super().insert_dependent_data(result, context)
