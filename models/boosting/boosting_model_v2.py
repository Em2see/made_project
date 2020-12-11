# import multiprocessing
import math
import datetime
import copy
from collections import defaultdict
from functools import lru_cache


import xgboost as xgb
import numpy as np
import pandas as pd
from .grid import Grid


class Model:
    def __init__(self, params: dict = None):
        params = copy.deepcopy(params) if params is not None else {}
        default_params = {
            'feb_trf_5': 56290839,
            'feb_trf_249': 471020780,

            # grid
            'grid_min': -10000,
            'grid_max': 10000,
            'grid_cell_size': 250,

            'cell_distance': 1000,
            'cell_angle': 60,

            # other
            'unique_tech': [2, 4, 5, 9],
            'last_year_5_trf_sum': 57101409.79213476,
            'last_year_294_trf_sum': 377548671.4183321,

            'xgboost_params': {
                'colsample_bylevel': 0.6,
                'colsample_bytree': 0.8,
                'gamma': 0.5,
                'learning_rate': 0.3,
                'max_depth': 3,
                'n_estimators': 180,
                'reg_alpha': 1.7,
                'reg_lambda': 1.9
            },
            # 'xgboost_params': {
            #     'n_estimators': 50,
            # },
        }
        for k, v in default_params.items():
            if k not in params:
                params[k] = v
        self.params = params

        self.grid = Grid(params['grid_min'], params['grid_max'],
                         params['grid_cell_size'], params['cell_distance'], params['cell_angle'])

        tech_5_trf_corr_coef = self.params.get('feb_trf_5') / self.params['last_year_5_trf_sum']
        tech_294_trf_corr_coef = self.params.get('feb_trf_249') / self.params['last_year_294_trf_sum']
        self.feb_trf_cor_coef = {5: tech_5_trf_corr_coef, 2: tech_294_trf_corr_coef,
                                 4: tech_294_trf_corr_coef, 9: tech_294_trf_corr_coef}

    def set_params(self, new_params: dict):
        for param, value in new_params.items():
            self.params.update({param: value})

        tech_5_trf_corr_coef = self.params.get('feb_trf_5') / self.params['last_year_5_trf_sum']
        tech_294_trf_corr_coef = self.params.get('feb_trf_249') / self.params['last_year_294_trf_sum']
        self.feb_trf_cor_coef = {5: tech_5_trf_corr_coef, 2: tech_294_trf_corr_coef,
                                 4: tech_294_trf_corr_coef, 9: tech_294_trf_corr_coef}

    def train(self, train_df: pd.DataFrame):
        train_df = train_df.copy()

        self.prepare_projections(train_df)
        self.prepare_grids(train_df)

        features = self.make_features(train_df)
        self.train_features = features

        model = xgb.XGBRegressor(**self.params['xgboost_params'])
        model.fit(features, train_df.spd)

        self.model = model

    def prepare_grids(self, dataset):

        # init traffic and subs grids
        trf_grid = {tech: self.grid.new_grid() for tech in self.params['unique_tech']}
        subs_grid = {tech: self.grid.new_grid() for tech in self.params['unique_tech']}

        # fill grids
        for cell_x, cell_y, cell_azimuth, subs, trf, tech in \
                dataset[['x', 'y', 'azimuth', 'subs', 'trf', 'tech']].values:
            grid_points = self.grid.get_grid_points_for_cell(cell_x, cell_y, cell_azimuth)

            trf_grid[tech].ravel()[grid_points] += trf / len(grid_points)
            subs_grid[tech].ravel()[grid_points] += subs / len(grid_points)

        # normalize grids
        for tech in self.params['unique_tech']:
            trf_grid[tech] = trf_grid[tech] * 100 / trf_grid[tech].sum()
            subs_grid[tech] = subs_grid[tech] * 100 / subs_grid[tech].sum()

        self.trf_grid_for_tech = trf_grid
        self.subs_grid_for_tech = subs_grid

    def get_cell_grids_for_df(self, dataset):
        df = dataset
        if 'date_str' not in df.columns.tolist():
            df.date_str = df.date_.astype(str)

        dates = df.date_str.unique()
        grid_for_date_tech = {date: {tech: self.grid.new_grid()
                                     for tech in self.params['unique_tech']} for date in dates}

        for date_ in dates:
            local_df = df[df.date_str == date_]

            for cell_x, cell_y, cell_azimuth, tech in \
                    local_df[['x', 'y', 'azimuth', 'tech']].values:
                grid_points = self.grid.get_grid_points_for_cell(cell_x, cell_y, cell_azimuth)
                grid_for_date_tech[date_][tech].ravel()[grid_points] += 1

        return grid_for_date_tech

    def prepare_projections(self, dataset):
        stat_df = dataset.groupby(['date_', 'tech']).agg({'subs': 'sum', 'trf': 'sum'})
        stat_df.reset_index(inplace=True, drop=False)

        proj_df = stat_df.copy()
        proj_df['date_'] = proj_df.date_.apply(lambda x: x + datetime.timedelta(days=364))

        proj_df = pd.concat([stat_df, proj_df[~proj_df.date_.isin(stat_df.date_.unique())]])

        proj_df.date_ = proj_df.date_.astype(str)
        proj_df.set_index(['date_', 'tech'], inplace=True)

        self.proj_df = proj_df

        subs_for_date_tech = proj_df.subs.to_dict()
        trf_for_date_tech = proj_df.trf.to_dict()

        self.subs_for_date_tech = subs_for_date_tech
        self.trf_for_date_tech = trf_for_date_tech

    def make_features(self, dataset):
        if 'weekday' not in dataset.columns.tolist():
            dataset['weekday'] = dataset.date_.apply(lambda x: x.weekday())
        if 'date_str' not in dataset.columns.tolist():
            dataset['date_str'] = dataset.date_.astype(str)

        num_cells_grid = self.get_cell_grids_for_df(dataset)

        features = []
        feature_names = [
            'weekday', 'height', 'tech',

            'trf_min', 'trf_max', 'trf_mean', 'trf_sum', 'trf_std',
            'subs_min', 'subs_max', 'subs_mean', 'subs_sum', 'subs_std',
            'num_cells_min', 'num_cells_max', 'num_cells_mean', 'num_cells_sum', 'num_cells_std',
        ]

        for cell_x, cell_y, cell_azimuth, tech, weekday, height, date_str in \
                dataset[['x', 'y', 'azimuth', 'tech', 'weekday', 'height', 'date_str']].values:
            grid_points = self.grid.get_grid_points_for_cell(cell_x, cell_y, cell_azimuth)

            l_ft = []
            l_ft.extend([weekday, height, tech])

            if (date_str, tech) in self.trf_for_date_tech:
                trf_coeff = self.trf_for_date_tech[(date_str, tech)]
            else:
                trf_coeff = self.trf_for_date_tech[('2016-10-30', tech)]
            trf_grid_l = (self.trf_grid_for_tech[tech].ravel() * trf_coeff)[grid_points]
            trf_min = trf_grid_l.min()
            trf_max = trf_grid_l.max()
            trf_mean = trf_grid_l.mean()
            trf_sum = trf_grid_l.sum()
            trf_std = trf_grid_l.std()
            l_ft.extend([trf_min, trf_max, trf_mean, trf_sum, trf_std])

            if (date_str, tech) in self.subs_for_date_tech:
                subs_coeff = self.subs_for_date_tech[(date_str, tech)]
            else:
                subs_coeff = self.subs_for_date_tech[('2016-10-30', tech)]
            subs_grid_l = (self.subs_grid_for_tech[tech].ravel() * subs_coeff)[grid_points]
            subs_min = subs_grid_l.min()
            subs_max = subs_grid_l.max()
            subs_mean = subs_grid_l.mean()
            subs_sum = subs_grid_l.sum()
            subs_std = subs_grid_l.std()
            l_ft.extend([subs_min, subs_max, subs_mean, subs_sum, subs_std])

            num_cells_grid_l = num_cells_grid[date_str][tech].ravel()[grid_points]
            num_cells_min = num_cells_grid_l.min()
            num_cells_max = num_cells_grid_l.max()
            num_cells_mean = num_cells_grid_l.mean()
            num_cells_sum = num_cells_grid_l.sum()
            num_cells_std = num_cells_grid_l.std()
            l_ft.extend([num_cells_min, num_cells_max, num_cells_mean, num_cells_sum, num_cells_std])

            features.append(l_ft)
        data = pd.DataFrame(data=features, columns=feature_names)

        data['trf_mean__div__num_cells_mean'] = data['trf_mean'] / data['num_cells_mean']
        data['trf_sum__div__num_cells_mean'] = data['trf_sum'] / data['num_cells_mean']

        return data

    def predict(self, test_df: pd.DataFrame):
        assert all([col in test_df.columns for col in ['x', 'y', 'azimuth',
                                                       'tech', 'date_', 'height', 'id']]), \
            "columns ['x', 'y', 'azimuth','tech', 'date_',\
            'height', 'id'] must be in test_df"

        # check if test_df is the same set of cells as the last time prediction was run
        # if it is, just reuse already calculated features and apply traffic projection
        if hasattr(self, 'test_df') and test_df[['id', 'tech', 'date_', 'x', 'y', 'azimuth']]\
                .equals(self.test_df[['id', 'tech', 'date_', 'x', 'y', 'azimuth']]):
            test_df = self.test_df
            features = self.features.copy()
        else:
            test_df = test_df.copy()
            self.test_df = test_df

            features = self.make_features(test_df)
            self.features = features.copy()

        # apply traffic projections
        features['_trf_coef'] = test_df[['date_str', 'tech']]\
            .apply(lambda row: self.feb_trf_cor_coef[row['tech']] if row['date_str'][:7] == '2017-02' else 1, axis=1)\
            .values
        features['trf_min'] = features['trf_min'] * features['_trf_coef']
        features['trf_max'] = features['trf_max'] * features['_trf_coef']
        features['trf_mean'] = features['trf_mean'] * features['_trf_coef']
        features['trf_sum'] = features['trf_sum'] * features['_trf_coef']
        features['trf_mean__div__num_cells_mean'] = features['trf_mean__div__num_cells_mean'] * features['_trf_coef']
        features['trf_sum__div__num_cells_mean'] = features['trf_sum__div__num_cells_mean'] * features['_trf_coef']
        features.drop(columns='_trf_coef', inplace=True)

        # self.features_after_corr = features.copy()

        prediction = self.model.predict(features)
        test_df['spd_pred'] = [max(x, 0) for x in prediction]

        return test_df
