from dataclasses import dataclass
from dataclasses import field
from types import GenericAlias
from types import UnionType
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generic
from typing import get_origin
from typing import List
from typing import Optional
from typing import Self
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union

from at_ontology_parser.base import OntologyBase
from at_ontology_parser.exceptions import Context
from at_ontology_parser.exceptions import OntologyException


T = TypeVar("T", bound=OntologyBase)
OWNER = TypeVar("OWNER", bound=OntologyBase)


class OntologyRefMeta(type):
    _generic_types = None

    def __getitem__(cls, key: Union[TypeVar, Tuple[TypeVar]]):
        args = key if isinstance(key, tuple) else (key,)
        if not len(args):
            raise TypeError(
                """Allowed only to use OntologyReference[Type] like OntologyReference[VertexType]
or OntologyReference[Union[VertexTemplate, VertexType]]"""
            )
        cls._generic_types = args
        return GenericAlias(cls, args)


def with_metaclass(meta):
    """
    A decorator to apply a metaclass to a class without explicitly specifying it.
    """

    def decorator(cls):
        return meta(cls.__name__, cls.__bases__, dict(cls.__dict__))

    return decorator


@dataclass(kw_only=True)
class AbstractReference(OntologyBase):
    alias: str
    value: Any = field(init=False, default=None)
    context: Context
    owner: Optional[OntologyBase] = field(init=False, default=None, repr=False)

    def _to_repr(self, context: Context, minify=True, exclude_name=True) -> Dict | str:
        return self.alias

    @property
    def fulfilled(self):
        return self.value is not None

    def request_fulfilling(self, raise_on_no_parser=False):
        if not self.context.parser:
            if raise_on_no_parser:
                raise OntologyException("No parser found in the context", context=self.context)
            return

        return self.context.parser.request_reference(self)

    def finalize(self) -> bool:
        if not self.has_owner:
            raise OntologyException("Owner is not set for the reference", context=self.context)
        return self.fulfilled


@with_metaclass(OntologyRefMeta)
@dataclass(kw_only=True)
class BaseReference(AbstractReference, Generic[T]):
    alias: str
    value: Optional[T] = field(init=False, default=None)
    context: Context
    owner: Optional[OntologyBase] = field(init=False, default=None, repr=False)
    _obj_generic_types: List[Type] = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if not hasattr(self.__class__, "_generic_types") or not self.__class__._generic_types:
            raise OntologyException(
                f"""Allowed only to use {self.__class__.__name__}[Type]
like {self.__class__.__name__}[VertexType] or {self.__class__.__name__}[Vertex | VertexType]""",
                context=self.context,
            )
        self._obj_generic_types = [t for t in self.__class__._generic_types]

    @property
    def types(self) -> List[Type[T]]:
        tp = self._obj_generic_types[0]

        if get_origin(tp) is Union or tp.__class__ is UnionType:
            result = list(tp.__args__)
        else:
            result = [tp]
        return [t for t in result]


@dataclass(kw_only=True)
class OntologyReference(BaseReference, Generic[T]):
    value: Optional[T] = field(init=False, default=None)

    def __post_init__(self) -> None:
        super().__post_init__()

        if len(list(self._generic_types)) != 1:
            raise OntologyException(
                f"""Allowed only to use {self.__class__.__name__}[Type] only with one type or Union of types
like {self.__class__.__name__}[VertexType] or {self.__class__.__name__}[Vertex | VertexType]""",
                context=self.context,
            )

        if self.context.parser:
            self.request_fulfilling()


def modify_owner_feature_ref_init(cls):
    old_init = cls.__init__

    def new_init(self, *args, **kwargs):
        if not hasattr(self, "__feature_getter__") or self.__feature_getter__ is None:
            raise TypeError(f"Use {self.__class__.__name__}.create(...) to create instances of this class")
        else:
            return old_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls


@modify_owner_feature_ref_init
@dataclass(kw_only=True)
class OwnerFeatureReference(BaseReference, Generic[T, OWNER]):
    value: Optional[T] = field(init=False, default=None)
    __feature_getter__: Callable[[OWNER, Self], T] = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        if len(list(self._obj_generic_types)) != 2:
            raise OntologyException(
                f"""Allowed only to use {self.__class__.__name__}[Type, OwnerType] only with two types
for example {self.__class__.__name__}[NodeTemplate, OperationImplementationDefinition] means
that reference will be fulfilled with a concrete NodeTemplate,
that is reffered in OperationImplementationDefinition field""",
                context=self.context,
            )

    @classmethod
    def create(
        cls, alias: str, context: Context, feature_getter: Callable[[OWNER, Self], T], owner: Optional[OWNER]
    ) -> "OwnerFeatureReference[T, OWNER]":
        ref = cls.__new__(cls)
        ref.alias = alias
        ref.context = context
        ref._obj_generic_types = [t for t in cls._generic_types]

        ref.__feature_getter__ = feature_getter
        ref.owner = owner
        ref.request_fulfilling()
        return ref
