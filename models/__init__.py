from .arma import Model as ARMA_model
from .boosting import Model as Boosting_model
from .linear import Model as Linear_model

from .arma import __description__ as ARMA_desc , __html__ as ARMA_html
from .boosting import __description__ as Boosting_desc , __html__ as Boosting_html
from .linear import __description__ as Linear_desc , __html__ as Linear_html

models_info = {
    "arma": (ARMA_desc, ARMA_html),
    "boosting": (Boosting_desc, Boosting_html),
    "linear": (Linear_desc, Linear_html)
}
