from src.exception import CustomException
import sys
import numpy as np
from typing import List
import tensorflow as tf
from src.utils import load_obj
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation

class Predict:
    def __init__(self):
        self.scaler = load_obj('/backend/artifacts/scaler.pkl')

    def running_predict(self, model_path: str, stock: str, days_ahead: int = 7) -> List[float]:
        '''
        Predicts the next `days_ahead` closing prices for a given stock using a hybrid DL model.

        Args:
            model_path: Path to the saved Keras or PyTorch model object.
            stock: Stock ticker symbol (e.g., 'AAPL').
            days_ahead: Number of days to predict into the future.

        Returns:
            List of predicted close prices for the next days.
        '''
        try:
            ingestion = DataIngestion(stock)
            data = ingestion.initiate_data_ingestion(interval='1day')

            transformation = DataTransformation()
            _, _,_, scaled_data, features = transformation.initiate_data_transformation(data)
            seq_len = transformation.sequence_length

            model = load_obj(model_path)
            input_sequence = scaled_data[-seq_len:].copy()
            predictions = []

            for _ in range(days_ahead):
                last_sequence = input_sequence.reshape((1, seq_len, len(features)))
                next_day_pred_scaled = model.predict(last_sequence)[0][0]  # Predict scaled close

                # Prepare feature vector for the next day: predicted close + replicate other features
                new_entry = input_sequence[-1].copy()  # Copy last known feature set
                new_entry[0] = next_day_pred_scaled    # Overwrite close with predicted value

                # For true exogenous features, update here as needed

                # Inverse transform to get price
                next_day_pred_full = np.zeros((1, len(features)))
                next_day_pred_full[0, 0] = next_day_pred_scaled
                next_day_pred_price = self.scaler.inverse_transform(next_day_pred_full)[0, 0]
                predictions.append(round(next_day_pred_price, 2))

                input_sequence = np.vstack([input_sequence[1:], new_entry])

            
            return predictions

        except Exception as e:
            raise CustomException(e, sys)
    
    def predict_cnn(self,model_path,stock_symbol,days_ahead):
        try:
            ingestor=DataIngestion(stock_symbol=stock_symbol)
            df=ingestor.fin_data_ingestion()
            transformer=DataTransformation()
            X_seq_scaled,X_ind_scaled,_,_,scaler_y=transformer.fin_data_transform(df=df)
            seq_len=transformer.sequence_length
            model=load_obj(model_path)
            predictions=[]
            x_seq_latest=X_seq_scaled.iloc[-seq_len:]
            x_ind_latest=X_ind_scaled.iloc[-seq_len:]
            
            for _ in range(days_ahead):
                y_pred_scaled=model.predict([x_seq_latest,x_ind_latest])
                y_pred_scaled=y_pred_scaled.numpy().reshape(-1) if isinstance(y_pred_scaled,tf.Tensor) else y_pred_scaled.reshape(-1)
                y_pred=scaler_y.inverse_transform(y_pred_scaled.reshape(-1,1).flatten()[0])
                predictions.append(y_pred)
                
                next_seq=x_seq_latest[:,1:,:].copy()
                new_seq_step=np.zeros((1,1,x_seq_latest.shape[2]))
                new_seq_step[0,0,0]=y_pred
                
                new_seq_step[0,0,1:]=x_seq_latest[0,-1,1:]
                x_seq_latest=np.concatenate([next_seq,next_seq_step],axis=1)
                
                new_ind=x_ind_latest[:,1:,:].copy()
                new_ind_step=x_ind_latest[:,-1,:].copy()
                x_ind_latest=np.concatenate([new_ind,new_ind_step],axis=1)
                
            return {
                "stock_symbol":stock_symbol,
                "next_n_pred":predictions
            }
        except Exception as e:
            raise CustomException(e,sys)
            
            