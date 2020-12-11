import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
import warnings
from .holt_winters import HoltWinters
warnings.simplefilter("ignore")

class Model():
    def __init__(self):
        '''
        Есть экспертная оценка во сколько раз изменится трафик.
        Аналогичная модель предсказала трафик - путем сравнения
        результатов предсказания и экспертной оценки был выбран 
        поправочный коэффициент - вес модели и экспертной оценки
        одинаковый
        '''
        self.alpha_final = 0.015
        self.beta_final = 0.0125
        self.gamma_final = 0.2
        self.slen = 30 # сезонность
        self.pred_depth = 120 # минимальная длина ряда
        self.col_target = 'trf_pred'
        self.col_source = 'trf'
        self.model_cat = CatBoostRegressor(iterations=300,
                          depth=5,
                          l2_leaf_reg=1,
                          learning_rate=0.3,
                          loss_function='MAPE',
                          logging_level='Silent')
        
        
    def train(self, train_df: pd.DataFrame):
        self.train = train_df.copy()
        self.train.sort_values(['id', 'date_', 'tech'], inplace=True)
        self.base_list = set(train_df['id'].tolist())
        self.train['date_cut'] = self.train['date_'].apply(lambda x: x.day)
        X = self.train[['trf','tech', 'date_cut']]
        y = self.train['spd']
        self.model_cat.fit(X, y)

    def predict_series(self):
        '''
        Если есть в трейне id , то строим тренд
        Если нет - то берем среднее
        '''
        self.diff_list = set(self.test['id'].tolist()).difference(set(self.train['id'].tolist()))

        frames = []
        for cell in self.base_list:
          sr_train = self.train[self.train['id']==cell][self.col_source]
          sr_test = self.test[self.test['id']==cell]
          spd_pred = sr_train.tolist()

          if(len(spd_pred) > self.pred_depth):
            model = HoltWinters(spd_pred, slen = self.slen,
                              alpha = self.alpha_final, beta = self.beta_final,
                              gamma = self.gamma_final, n_preds = len(sr_test))
            
            model.triple_exponential_smoothing()          
            sr_test[self.col_target] = model.result[-len(sr_test):]
            frames.append(sr_test)
          else:
           self.diff_list.add(cell)

        result = pd.concat(frames)
        result['date_cut_'] = result['date_'].apply(lambda x: x.strftime('%Y-%m'))
        df_agg = result.groupby(['tech', 'cap', 'date_cut_'])[self.col_target].mean().to_dict()
        frame_diff = []
        self.test['date_cut_'] = self.test['date_'].apply(lambda x: x.strftime('%Y-%m'))
        for cell in self.diff_list:
          sr_test = self.test[self.test['id']==cell]
          sr_test[self.col_target] = sr_test.apply(lambda x: df_agg[(x['tech'],x['cap'],x['date_cut_'])], axis=1)
          frame_diff.append(sr_test)
        result_diff = pd.concat(frame_diff)
        spd_df_result = pd.concat([result_diff, result])
        spd_df_result.sort_values(['id', 'date_', 'tech'], inplace=True)
        return spd_df_result[self.col_target]

    def predict(self, test_df: pd.DataFrame):
      '''
      Пробуем восстановить скорость через трафик
      '''
      self.test = test_df.copy()
      self.test.sort_values(['id', 'date_', 'tech'], inplace=True)
      #self.test['date_cut'] = self.test['date_'].apply(lambda x: float(x[8:10]))
      self.test['date_cut'] = self.test['date_'].apply(lambda x: x.day)
      self.test['trf'] = self.predict_series()
      self.test['spd_pred'] = self.model_cat.predict(self.test[['trf','tech', 'date_cut']])
      return self.test