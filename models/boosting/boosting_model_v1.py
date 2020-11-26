# import multiprocessing
import math
import datetime
from collections import defaultdict
from copy import copy

import xgboost as xgb
import numpy as np
import pandas as pd


class Model():
    def __init__(self, params: dict = None):
        params = opy(params) if params is not None else {}
        if 'feb_trf_5' not in params:
            params['feb_trf_5'] = 56290839
        if 'feb_trf_249' not in params:
            params['feb_trf_249'] = 471020780
        self.params = params
    
    def set_params(self, new_params: dict):
        for param, value in new_params.items():
            self.params.update({param: value})
    
    def train(self, train_df: pd.DataFrame):
        train_df = train_df.copy()
        
        self.prepare_projections(train_df)
        self.prepare_grids(train_df)
        
        features = self.make_features(train_df)
        
        model = xgb.XGBRegressor(n_estimators=150, learning_rate=0.6)
        model.fit(features, train_df.spd)
        
        self.model = model
        
    def prepare_grids(self, dataset):
        grid_min, grid_max = -10000, 10000
        grid_cell_size = 250
        grid = np.zeros(((grid_max - grid_min) // grid_cell_size, (grid_max - grid_min) // grid_cell_size))
        self.grid = grid
        grid_speed = np.zeros_like(grid)
        grid_cell_count = np.zeros_like(grid)

        def get_grid_idx(x, y):
            return (x // grid_cell_size) - (grid_min // grid_cell_size), (y // grid_cell_size) - (grid_min // grid_cell_size),

        def grid_to_xy(i, j):
            return (i + (grid_min // grid_cell_size)) * grid_cell_size - grid_cell_size/2.0,\
                   (j + (grid_min // grid_cell_size)) * grid_cell_size - grid_cell_size/2.0,

        ijs = np.array([[i,j] for i in range(grid.shape[0]) for j in range(grid.shape[1])])
        xy_points = np.array([list(grid_to_xy(i,j)) for i,j in ijs])

        def get_grid_points_for_cell(cell_x, cell_y, cell_azimuth, grid_cell_size, grid_min, grid_max, dist=1000, angle=60):
            xy_cell = np.array([cell_x, cell_y]).reshape(-1, 2).repeat(len(xy_points), axis=0)
            distances = np.linalg.norm(xy_cell - xy_points, axis=1)

            azimuth_vectors = np.array([np.cos((360 - cell_azimuth + 90) / 180 * np.pi),\
                                        np.sin((360 - cell_azimuth + 90) / 180 * np.pi)])\
            .reshape(-1, 2).repeat(len(xy_points), axis=0)

            azimuth_vectors = azimuth_vectors / np.linalg.norm(azimuth_vectors[0,:])

            direction_vectors = xy_points - xy_cell

            direction_vectors = direction_vectors / np.linalg.norm(direction_vectors, axis=1).reshape(direction_vectors.shape[0], -1)

            angles = np.arccos(np.einsum('ij,ij->i', direction_vectors,azimuth_vectors)) / np.pi * 180

            result = []
            for i, (angle_b, dist_b) in enumerate(zip(angles, distances)):
                if dist_b <= dist and angle_b <= angle:
                    result.append(i)
            return result

        class DDict(dict):
            def __init__(self, factory):
                self.factory = factory
            def __missing__(self, key):
                self[key] = self.factory(key)
                return self[key]


        grid_points_for_cell_params = DDict(lambda t: get_grid_points_for_cell(t[0],t[1],t[2],
                                                                             grid_cell_size,grid_min, grid_max))


#         def pool_func(tup):
#             cell_x, cell_y, cell_azimuth, grid_cell_size, grid_min, grid_max = tup
#             return [(cell_x, cell_y, cell_azimuth), get_grid_points_for_cell(cell_x,cell_y,cell_azimuth,
#                                                                              grid_cell_size,grid_min, grid_max)]

#         values = dataset[['x','y','azimuth']].drop_duplicates().values
#         with multiprocessing.Pool(8) as pool:
#             result = pool.map(pool_func,
#                               list(zip(values[:,0], values[:,1], values[:,2], [grid_cell_size]*values.shape[0],
#                                                                               [grid_min]*values.shape[0],
#                                                                               [grid_max]*values.shape[0]
#                               )),
#                               chunksize=50)
            
#         for key, value in result:
#             grid_points_for_cell_params[key] = value
            
        trf_grid_for_tech = defaultdict(lambda: np.zeros_like(grid))
        sum_subs_grid_for_tech = defaultdict(lambda: np.zeros_like(grid))
        
        for cell_x, cell_y, cell_azimuth, subs, spd, trf, tech in \
                dataset[['x', 'y', 'azimuth', 'subs', 'spd', 'trf', 'tech']].values:
            grid_points = grid_points_for_cell_params[(cell_x, cell_y, cell_azimuth)]

            trf_grid_for_tech[tech].ravel()[grid_points] += trf / len(grid_points)
            sum_subs_grid_for_tech[tech].ravel()[grid_points] += subs / len(grid_points)
        
        for key in trf_grid_for_tech.keys():
            trf_grid_for_tech[key] = trf_grid_for_tech[key] * 100 / trf_grid_for_tech[key].sum()
            sum_subs_grid_for_tech[key] = sum_subs_grid_for_tech[key] * 100 / sum_subs_grid_for_tech[key].sum()
            
        self.trf_grid_for_tech = trf_grid_for_tech
        self.subs_grid_for_tech = sum_subs_grid_for_tech
        
        self.grid_points_for_cell_params = grid_points_for_cell_params
        
    def get_cell_grids_for_df(self, dataset):
        df = dataset.copy()
        df.date_ = df.date_.astype(str)

        grid_for_date_tech = defaultdict(lambda : defaultdict(lambda : np.zeros_like(self.grid)))

        for date_ in df.date_.unique():
            local_df = df[df.date_ == date_]

            for cell_x, cell_y, cell_azimuth, tech in \
                local_df[['x', 'y', 'azimuth', 'tech']].values:
                grid_points = self.grid_points_for_cell_params[(cell_x, cell_y, cell_azimuth)]
                grid_for_date_tech[date_][tech].ravel()[grid_points] += 1

        return grid_for_date_tech
        
    def prepare_projections(self, dataset):
        last_year_5_trf_sum = dataset[dataset.date_.apply(lambda x: x.month == 2) & (dataset.tech == 5)].trf.sum()
        last_year_294_trf_sum = dataset[dataset.date_.apply(lambda x: x.month == 2) & (dataset.tech != 5)].trf.sum()
        
        tech_5_trf_corr_coef = self.params.get('feb_trf_5') / last_year_5_trf_sum
        tech_294_trf_corr_coef = self.params.get('feb_trf_249') / last_year_294_trf_sum

        test_trf_correct_coeff_for_tech = {}
        test_trf_correct_coeff_for_tech[5] = tech_5_trf_corr_coef
        test_trf_correct_coeff_for_tech[2] = tech_294_trf_corr_coef
        test_trf_correct_coeff_for_tech[4] = tech_294_trf_corr_coef
        test_trf_correct_coeff_for_tech[9] = tech_294_trf_corr_coef

        stat_df = dataset.groupby(['date_', 'tech']).agg({'subs' : 'sum', 'trf' : 'sum'})
        stat_df.reset_index(inplace=True, drop=False)

        proj_df = dataset.groupby(['date_', 'tech']).agg({'subs' : 'sum', 'trf' : 'sum'})
        proj_df.reset_index(inplace=True, drop=False)
        proj_df['date_'] = proj_df.date_.apply(lambda x: x + datetime.timedelta(days=364))

        proj_df = pd.concat([stat_df, proj_df[~proj_df.date_.isin(stat_df.date_.unique())]])
        
        proj_df.loc[(proj_df.date_ >= '2017-01-01') & (proj_df.date_ < '2017-02-01'), 'trf'] = \
        proj_df[(proj_df.date_ >= '2017-01-01') & (proj_df.date_ < '2017-02-01')][['trf', 'tech']]\
            .apply(lambda row: row['trf'] * test_trf_correct_coeff_for_tech[row['tech']], axis=1)
        
        proj_df.date_ = proj_df.date_.astype(str)
        proj_df.set_index(['date_', 'tech'], inplace=True)
        
        subs_for_date_tech = proj_df.subs.to_dict()
        trf_for_date_tech = proj_df.trf.to_dict()
        
        self.subs_for_date_tech = subs_for_date_tech
        self.trf_for_date_tech = trf_for_date_tech
        
    def make_features(self, dataset):
        dataset = dataset.copy()
        dataset['weekday'] = dataset.date_.apply(lambda x: x.weekday())
        dataset['date_str'] = dataset.date_.astype(str)

        num_cells_grid = self.get_cell_grids_for_df(dataset)

        features = []
        feature_names = [
            'weekday', 'height', 'tech',

            'trf_min', 'trf_max', 'trf_mean', 'trf_sum', 'trf_std',
            'subs_min', 'subs_max', 'subs_mean', 'subs_sum', 'subs_std',
            'num_cells_min', 'num_cells_max', 'num_cells_mean', 'num_cells_sum', 'num_cells_std',
        ]

    #     points_df = dataset[['date_str', 'x', 'y']].drop_duplicates()
    #     distances = {}
    #     xys = points_df[['x', 'y']].drop_duplicates()
    #     for x1,y1 in xys.values:
    #         for x2, y2 in xys.values:
    #             distances[((x1, y1), (x2, y2))] = math.sqrt((x1-x2)^2 + (y1-y2)^2)


        for cell_x, cell_y, cell_azimuth, tech, weekday, height, date_str in \
            dataset\
            [['x', 'y', 'azimuth', 'tech', 'weekday', 'height', 'date_str']].values:
            grid_points = self.grid_points_for_cell_params[(cell_x, cell_y, cell_azimuth)]

            l_ft = []
            l_ft.extend([weekday, height, tech])

            if (date_str, tech) in self.trf_for_date_tech:
                trf_coeff = self.trf_for_date_tech[(date_str,tech)]
            else:
                trf_coeff = self.trf_for_date_tech[('2016-10-30',tech)]
            trf_grid_l = (self.trf_grid_for_tech[tech].ravel() * trf_coeff)[grid_points]
            trf_min =  trf_grid_l.min()  
            trf_max =  trf_grid_l.max()  
            trf_mean = trf_grid_l.mean() 
            trf_sum =  trf_grid_l.sum()  
            trf_std =  trf_grid_l.std()  
            l_ft.extend([trf_min, trf_max, trf_mean, trf_sum, trf_std]) 

            
            if (date_str, tech) in self.subs_for_date_tech:
                subs_coeff = self.subs_for_date_tech[(date_str,tech)]
            else:
                subs_coeff = self.subs_for_date_tech[('2016-10-30',tech)]
            subs_grid_l = (self.subs_grid_for_tech[tech].ravel() * subs_coeff)[grid_points]
            subs_min =  subs_grid_l.min() 
            subs_max =  subs_grid_l.max() 
            subs_mean = subs_grid_l.mean()
            subs_sum =  subs_grid_l.sum() 
            subs_std =  subs_grid_l.std() 
            l_ft.extend([subs_min, subs_max, subs_mean, subs_sum, subs_std]) 

            num_cells_grid_l = num_cells_grid[date_str][tech].ravel()[grid_points]
            num_cells_min =  num_cells_grid_l.min() 
            num_cells_max =  num_cells_grid_l.max() 
            num_cells_mean = num_cells_grid_l.mean()
            num_cells_sum =  num_cells_grid_l.sum() 
            num_cells_std =  num_cells_grid_l.std() 
            l_ft.extend([num_cells_min, num_cells_max, num_cells_mean, num_cells_sum, num_cells_std]) 


            features.append(l_ft)
        data = pd.DataFrame(data=features, columns=feature_names)

        data['trf_mean__div__num_cells_mean'] = data['trf_mean'] / data['num_cells_mean']
        data['trf_sum__div__num_cells_mean']  = data['trf_sum']  / data['num_cells_mean']

        return data
        
    
    def predict(self, test_df: pd.DataFrame):
        
        assert all([col in test_df.columns for col in ['x', 'y', 'azimuth',
                                                        'tech', 'date_', 'height', 'id']]),\
            "columns ['x', 'y', 'azimuth','tech', 'date_',\
            'height', 'id'] must be in test_df"
        
        features = self.make_features(test_df)
        prediction = self.model.predict(features)
        test_df['spd_pred'] = prediction
        
        return test_df
