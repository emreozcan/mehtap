from abc import ABC
from collections.abc import Mapping
from typing import Any

import attrs

DEBUG = True

if DEBUG:
    from pydantic import BaseModel
    attrs.define = lambda *a, **kw: (lambda x: x)

    def _asdict(v) -> dict | list | Any:
        if hasattr(v, "as_dict"):
            return {"__type__": v.__class__.__qualname__, **v.as_dict()}
        if isinstance(v, (dict, Mapping)):
            return {k: _asdict(v) for k, v in v.items()}
        if isinstance(v, (tuple, list)):
            return [_asdict(x) for x in v]
        return v

    class Node(BaseModel, ABC):
        def as_dict(self):
            return {
                "__type__": self.__class__.__qualname__,
                **{
                    k: _asdict(v)
                    for k, v in self.__dict__.items()
                }
            }
else:
    @attrs.define(slots=True)
    class Node(ABC):
        def as_dict(self):
            return attrs.asdict(self)
