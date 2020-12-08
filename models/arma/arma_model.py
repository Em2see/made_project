# import multiprocessing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

from scipy import stats
from statsmodels.tsa.arima_model import ARMA
from scipy.stats import boxcox
from scipy.special import inv_boxcox
from itertools import product
from datetime import datetime

import warnings
import sys
import os


class Model():
    def __init__(self, params: dict = None):
        def_path = os.path.dirname(os.path.abspath(__name__))
        data_path = os.path.join(def_path, "data")
        self.paths = {
            "default": def_path,
            "data": data_path,
            "params": os.path.join(data_path, "listofparams.npy")
        }
        
        
    def train(self, train_df: pd.DataFrame):
        idx = train_df.groupby('id').size()[train_df.groupby('id').size()==305].index.values
        self.listofparams = []

        for cell in idx:
            # формируем временной ряд для конкретной соты
            data = pd.DataFrame(train_df[(train_df['id'] == cell)][['date_', 'spd']].sort_values('date_'))
            data['date'] =  pd.to_datetime(data['date_'], format='%Y-%m-%d')
            data.drop('date_', axis=1, inplace=True)
            data.set_index('date', inplace=True)
            
            # делаем преобразование бокса-кокса для стабилизации дисперсии
            data['spd'], lmbda = stats.boxcox(data.spd + 1)
            
            # проверяем стационарность ряда через тест Дики-Фуллера
            if sm.tsa.stattools.adfuller(data.spd)[1] > 0.05:
                continue
            
            # задаем сетку параметров для перебора
            ps = [i for i in range(5)]
            qs = [i for i in range(3)]
            parameters = product(ps, qs)
            parameters_list = list(parameters)
            
            results = []
            best_param = None
            best_aic = float("inf")
            warnings.filterwarnings('ignore')
            
            # пробегаемся по сетке параметров. где возможно строим модель и оцениваем качество по AIC.
            for param in parameters_list:
                try:
                    model = ARMA(data.spd, order=(param[0], param[1])).fit(disp=-1)
                except:
                    continue
                aic = model.aic
                if aic < best_aic:
                    best_model = model
                    best_aic = aic
                    best_param = param
                results.append([param, model.aic])
            
            # сохраняем кортеж (сота-оптимальные параметры модели)
            self.listofparams.append((cell, best_param))
        
        self.train_df = train_df.copy(deep=True)
        
    def load_params(self, train_df: pd.DataFrame):
        self.train_df = train_df.copy(deep=True)
        self.listofparams = np.load(self.paths['params'], allow_pickle=True)
            
    def get_celldict(self, train_df: pd.DataFrame, test_df: pd.DataFrame):
        '''
        Делаем словарик предиктов для тех сот, которые есть в предыдущем списке.
        Подтягиваем параметры модели из списка, делаем предикт, 
        затем обратное преобразование Бокса-Кокса и записываем в словарик предиктов.
        '''

        celldict = {}
        validtest = test_df.groupby('id').size()[test_df.groupby('id').size()==120].index.values

        for i in range(len(self.listofparams)):
            cell, params = self.listofparams[i]
            
            if cell not in validtest:
                continue
            
            data = pd.DataFrame(train_df[(train_df['id'] == cell)][['date_', 'spd']].sort_values('date_'))
            data['date'] =  pd.to_datetime(data['date_'], format='%Y-%m-%d')
            data.drop('date_', axis=1, inplace=True)
            data.set_index('date', inplace=True)
            data['spd'], lmbda = boxcox(data.spd + 1)

            model = ARMA(data.spd, order=(params[0], params[1])).fit(disp=-1)
            yhat = model.predict(len(data), len(data)+119)
            preds = inv_boxcox(yhat, lmbda) - 1
            
            celldict[cell] = list(preds.values)
            
        return celldict
        
    def get_techdict(self, train_df: pd.DataFrame):
        '''
        Базовый словарик по средним значениям скорости соты в зависимости от tech
        '''

        techdict = dict()

        for tech in train_df['tech'].unique():
            techdict[tech] = train_df[(train_df['date_'] >= pd.to_datetime('2016-08-01'))&(train_df['tech'] == tech)]['spd'].mean()
            
        return techdict
        
    def get_celldict90(self, train_df: pd.DataFrame):
        '''
        Словарик по средним значениям скорости соты в исходя из последних ~90 дней
        '''

        celldict90 = dict()

        for cell in train_df['id'].unique():
            celldict90[cell] = train_df[(train_df['date_'] >= pd.to_datetime('2016-08-01'))&(train_df['id']==cell)]['spd'].mean()
            
        return celldict90
        
    def precalc_params(self, test_df: pd.DataFrame):
        self.celldict = self.get_celldict(self.train_df, test_df)
        self.techdict = self.get_techdict(self.train_df)
        self.celldict90 = self.get_celldict90(self.train_df)

    def predict(self, test_df: pd.DataFrame):
        
        self.precalc_params(test_df)
        
        preds = pd.DataFrame()
        preds['id'] = test_df['id']
        preds['date_'] = test_df['date_']
        preds.sort_values(['id', 'date_'], inplace=True, ascending=True)
        
        '''
        Делаем предикт. Если сота есть в словарике ARMA предиктов, то берем результат оттуда.
        Иначе берем средний результат за последние 90 дней из другого словарика.
        Если и его нет, то предиктом будет выступать среднее по tech соты за последние 90 дней.
        '''

        f = []

        for cell in preds['id'].unique():
            if cell in self.celldict:
                f.extend(self.celldict[cell])
                continue
            elif cell in self.celldict90:
                f.extend(test_df[test_df['id']==cell].shape[0] * [self.celldict90[cell]])
                continue
            else:
                tech = test_df[test_df['id'] == cell]['tech'].values[0]
                f.extend(test_df[test_df['id']==cell].shape[0] * [self.techdict[tech]])
                
        preds['spd'] = f
        
        ans = test_df.sort_values(['id', 'date_'], ascending=True)
        ans['spd_pred'] = preds['spd']
        ans.sort_index(inplace=True)
                
        return ans
