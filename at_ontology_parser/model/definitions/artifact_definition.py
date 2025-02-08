from dataclasses import dataclass
from dataclasses import field
from typing import Optional

from at_ontology_parser.base import Definition


@dataclass(kw_only=True)
class ArtifactDefinition(Definition):
    default_path: Optional[str] = field(default=None)
    mime_type: Optional[str] = field(default="application/octet-stream")
    required: Optional[bool] = field(default=False)
    allows_multiple: Optional[bool] = field(default=True)
    min_assignments: Optional[int] = field(default=None)
    max_assignments: Optional[int] = field(default=None)
