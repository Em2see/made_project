__author__ = 'Egor Kravchenko'
__email__ = 'egor.kravchenko@grr.la'
__version__ = '0.0.4'
__description__= 'Boosting model'
__tools__= 'xgboost numpy pandas'
__html__= """
<p>Модель использует историческое распределение трафика и абонентов по метсности для того, чтобы построить признаки на тестовых данных.
<br>
Модель может делать предсказания как для старых вышек, так и для совершенно новых, при этом появление новых вышек повлияет на предсказание соседних вышек.</p>
"""

from .boosting_model_v2 import Model