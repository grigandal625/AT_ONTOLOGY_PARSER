from typing import Any
from typing import Dict
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import Instancable
from at_ontology_parser.exceptions import Context
from at_ontology_parser.parsing.models.base import DerivableModel
from at_ontology_parser.parsing.models.model.definitions.artifact_definition import Artifacts
from at_ontology_parser.parsing.models.model.definitions.property_definition import Properties


class InstancableModel(DerivableModel):
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    properties: Optional[Properties] = Field(default_factory=lambda: Properties({}))
    artifacts: Optional[Artifacts] = Field(default_factory=lambda: Artifacts({}))

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
