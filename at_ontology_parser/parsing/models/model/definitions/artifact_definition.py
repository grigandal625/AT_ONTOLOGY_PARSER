from typing import Dict
from typing import Optional

from pydantic import Field

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.model.definitions import ArtifactDefinition
from at_ontology_parser.parsing.models.base import DefinitionModel
from at_ontology_parser.parsing.models.base import OntoRootModel


class ArtifactDefinitionModel(DefinitionModel):
    default_path: Optional[str] = Field(default=None)
    mime_type: str = Field(default="application/octet-stream")
    required: bool = Field(default=False)

    def get_preliminary_object(self, data, *, context: Context, owner: OntologyBase):
        result = ArtifactDefinition(**data)
        result.owner = owner
        return result


class Artifacts(OntoRootModel[Dict[str, ArtifactDefinitionModel]]):
    def _to_internal(self, *, context: Context, owner: OntologyBase, **kwargs):
        return {
            key: value.to_internal(context=context.create_child(key, data=value), owner=owner, name=key)
            for key, value in self.root.items()
        }
