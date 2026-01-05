from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from at_ontology_parser.base import OntologyBase


@dataclass(kw_only=True)
class ImportDefinition(OntologyBase):
    file: str
    alias: Optional[str] = field(default=None)

    def _to_repr(self, context, minify=True, exclude_name=True):
        if self.alias:
            return {self.alias: self.file}
        return self.file
