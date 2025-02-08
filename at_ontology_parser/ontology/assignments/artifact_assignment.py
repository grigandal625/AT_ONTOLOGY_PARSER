from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import TYPE_CHECKING
from uuid import uuid4

from at_ontology_parser.base import OntologyBase


if TYPE_CHECKING:
    from at_ontology_parser.model.definitions.artifact_definition import ArtifactDefinition
    from at_ontology_parser.reference import OwnerFeatureReference
    from at_ontology_parser.base import Instance
    from io import IOBase


@dataclass(kw_only=True)
class ArtifactAssignment(OntologyBase):
    id: str | int = field(default_factory=lambda: str(uuid4()))
    artifact: "OwnerFeatureReference[ArtifactDefinition, Instance]" = field(repr=False)
    path: Optional[str] = field(default=None)
    content: "IOBase" = field(repr=False, init=False)
