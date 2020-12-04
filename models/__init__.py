import os
from pathlib import Path
from pkgutil import iter_modules
from glob import glob
from importlib import import_module

package_dir = Path(__file__).resolve().parent

models_info = dict()
models_class = dict()

for (_, module_name, ispkg) in iter_modules([package_dir]):
    module = import_module(f"{__name__}.{module_name}")
    if ispkg:
        models_info[module_name] = [getattr(module,fname) for fname in ['__description__', '__html__']]
        class_name = module_name[0].upper() + module_name[1:] + "_model"
        globals()[class_name] = getattr(module, "Model")
        models_class[module_name] = getattr(module, "Model")
    else:
        globals()[module_name] = module
    