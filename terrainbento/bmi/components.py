import sys
import warnings

from terrainbento.derived_models import MODELS

from .bmi_bridge import wrap_as_bmi

__all__ = []
for cls in MODELS:
    try:
        as_bmi = wrap_as_bmi(cls)
    except TypeError:
        warnings.warn("unable to wrap class {name}".format(name=cls.__name__))
    else:
        setattr(sys.modules[__name__], as_bmi.__name__, as_bmi)
        __all__.append(as_bmi.__name__)