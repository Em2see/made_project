__author__ = 'Nikolay Popov'
__email__ = 'nikolay.popov@grr.la'
__version__ = '0.0.3'
__description__= 'Linear model'
__tools__= ''
__html__= """
<p>Модель на основе предсказания трафика с помощью экспоненциального сглаживания Винтер-Хольц и дальнейшее использование показателей трафика в качестве фичи для предсказания скорости для модели регрессии.
</p>
"""

from .linear_model import Model