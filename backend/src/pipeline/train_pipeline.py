from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_train import Model_Trainer
from src.components.two_stage_trainer import train_two_stage_and_persist
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
            x_seq, x_ind, y_return_scaled, y_dir, features, scaler_y = transformer.fin_data_transform(data)
            trainer=Model_Trainer()
            res = trainer.train_cnn_hybrid(symbol, x_seq, x_ind, y_return_scaled, y_dir, features, scaler_y)
            model_path = f'artifacts/models/{symbol}_cnn_hybrid.keras'
            save_object(model_path,res['best_model_object'])
            res['best_model_path']=model_path
            return res
        except Exception as e:
            raise CustomException(e,sys)

    def train_two_stage(self, symbol):
        """Main two-stage training entry: direction then return with proper scaling."""
        try:
            ingestor = DataIngestion(symbol)
            raw = ingestor.fin_data_ingestion()
            transformer = DataTransformation(sequence_length=30)
            result = train_two_stage_and_persist(symbol=symbol, data=raw, transformer_obj=transformer)
            return result
        except Exception as e:
            raise CustomException(e, sys)

    