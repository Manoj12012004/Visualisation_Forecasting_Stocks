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
            logging.info("Running Training Pipeline for model...")

            ingestion = DataIngestion(stock)
            data = ingestion.initiate_data_ingestion()

            transformation = DataTransformation()
            X,y,_,features = transformation.initiate_data_transformation(data)
            
            model=Model_Trainer()
            res=model.initiate_train(X,y,features)
            model_path = f"artifacts/{stock}_model.pkl"
            
            save_object(model_path,res['best_model_object'])
            res['best_model_path'] = model_path
            return res
        
        except Exception as e:
            raise CustomException(e,sys)

