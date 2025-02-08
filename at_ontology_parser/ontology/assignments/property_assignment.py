from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import TYPE_CHECKING
from uuid import uuid4

from at_ontology_parser.base import OntologyBase


if TYPE_CHECKING:
    from at_ontology_parser.model.definitions.property_definition import PropertyDefinition
    from at_ontology_parser.reference import OwnerFeatureReference
    from at_ontology_parser.base import Instance


@dataclass(kw_only=True)
class PropertyAssignment(OntologyBase):
    id: str | int = field(default_factory=lambda: str(uuid4()))
    property: "OwnerFeatureReference[PropertyDefinition, Instance]" = field(repr=False)
    value: Any = field(repr=False)
