from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from at_ontology_parser.base import OntologyBase


@dataclass(kw_only=True)
class ImportDefinition(OntologyBase):
    file: str
    alias: Optional[str] = field(default=None)
