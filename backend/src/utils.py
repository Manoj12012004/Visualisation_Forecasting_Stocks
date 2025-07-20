import os
import sys

import numpy as np
import pandas as pd
import dill

from src.exception import CustomException
from src.logger import logging
from sklearn.preprocessing import MinMaxScaler

def scalar():
    scaler = MinMaxScaler()
    return scaler
def save_object(file_path,obj):
    try:
        dir_path=os.path.dirname(file_path)
        os.makedirs(dir_path,exist_ok=True)
        
        with open(file_path,'wb') as file_obj:
            dill.dump(obj,file_obj)
    except Exception as e:
        return CustomException(e,sys)

def load_obj(file_path):
    with open(file_path,'rb')as file_obj:
        return dill.load(file_obj)