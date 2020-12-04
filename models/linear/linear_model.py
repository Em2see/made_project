import pandas as pd
import numpy as np

class Model:
    def __init__(self):
        self.spd = 0
        
    def train(self, train_df: pd.DataFrame):
        self.spd = np.mean(train_df['spd'])
        
    def predict(self, test_df: pd.DataFrame):
        df = pd.DataFrame(test_df)
        df['spd_pred'] = self.spd
        return df
