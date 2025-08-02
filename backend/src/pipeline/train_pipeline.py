from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_train import Model_Trainer
from src.logger import logging
from src.exception import CustomException
from src.utils import save_object
import sys
from pathlib import Path


class Train:
    def run_training_pipeline(self,stock):
        try:
            ingestion = DataIngestion(stock)
            data = ingestion.initiate_data_ingestion(interval='1day')

            transformation = DataTransformation()
            X,y,_,_,features = transformation.initiate_data_transformation(data)
            
            model=Model_Trainer()
            res=model.initiate_train(stock,X,y,features)
            model_path = f"artifacts/models/{stock}_model.keras"
            
            save_object(model_path,res['best_model_object'])
            res['best_model_path'] = model_path
            return res
        
        except Exception as e:
            raise CustomException(e,sys)
        
    def train_cnn(self,symbol):
        try:
            ingestor=DataIngestion(symbol)
            data=ingestor.fin_data_ingestion()
            transformer=DataTransformation()
            X_seq,X_ind,y,features,scalar=transformer.fin_data_transform(data)
            trainer=Model_Trainer()
            res=trainer.train_cnn(symbol,X_seq,X_ind,y,features=features,scaler_y=scalar)
            model_path=f'artifacts/models/{symbol}_cnn.keras'
            save_object(model_path,res['best_model_object'])
            res['best_model_path']=model_path
            return res
        except Exception as e:
            raise CustomException(e,sys)

