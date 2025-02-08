from dataclasses import dataclass
from typing import TYPE_CHECKING

from at_ontology_parser.base import Instancable

if TYPE_CHECKING:
    pass


@dataclass(kw_only=True)
class VertexType(Instancable):
    pass
