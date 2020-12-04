from . import models_class, models_info
import os
import numpy as np
import pandas as pd
from time import time

timer = None
time_sets = []

default_path = os.path.dirname(os.path.abspath(__file__))
def_train_path = os.path.join(default_path, './data/train_short.csv')
def_test_path = os.path.join(default_path, './data/pred_short.csv')

def init_timer():
    timer = time()
    time_sets.append(timer)
    
def print_timer(msg):
    time_sets.append(time())
    params = {"diff": time_sets[-1] - time_sets[-2]}
    return msg.format(**params)

def formater_pipe(df):
    df.columns = df.columns.str.lower()
    df['date_'] = pd.to_datetime(df['date_'])
    return df

def load_df(train_path, test_path):
    # pass
    _, ext = os.path.splitext(train_path)
    if ext == ".xlsx" or ext == ".xls":
        reader = pd.read_excel
    elif ext == ".pickle":
        reader = pd.read_pickle
    elif ext == ".csv":
        reader = pd.read_csv
    else:
        reader = None
    
    if reader:
        train_df = reader(train_path)
        train_df = train_df.pipe(formater_pipe)
        test_df = reader(test_path)
        test_df = test_df.pipe(formater_pipe)
        
    return train_df, test_df

def wrmse(spd_predict, spd, subs, util=None):
    return np.sqrt(np.sum( ((spd_predict - spd) * subs)**2) / np.sum(subs**2))

def test_all_models():
    
    train_df, test_df = load_df(def_train_path, def_test_path)
    for model_name, model_cls in models_class.items():
        print("testing of " + model_name)
        assert test_model(model_cls, model_name, train_df, test_df)

def test_model(model_cls, model_name, train_df, test_df, params=None):
    init_timer()
    if params:
        model = model_cls(**params)
    else:
        model = model_cls()
    print(print_timer(f"Model creation {model_name} took " + "{diff:.3f}"))
    
    model.train(train_df)
    print(print_timer(f"Train {model_name} took " + "{diff:.3f}"))
    
    predict_df = model.predict(test_df)
    print(print_timer(f"Predict {model_name} took " + "{diff:.3f}"))
    
    print("WRMSE {:.3f}".format(wrmse(predict_df['spd_pred'], test_df['spd'], test_df['subs'])))
    
    return True