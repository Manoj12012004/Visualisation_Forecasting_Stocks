from src.exception import CustomException
import sys
import numpy as np
from src.utils import load_obj
from src.components.data_ingestion import DataIngestion
from src.components.data_transformation import DataTransformation

class Predict:
    def __init__(self):
        self.scaler=load_obj('/backend/artifacts/scaler.pkl')
    def running_predict(self,model_path,stock):
        try:
            ingestion = DataIngestion(stock)
            data = ingestion.initiate_data_ingestion()

            transformation = DataTransformation()
            X,y,scaled_data,features= transformation.initiate_data_transformation(data)
            # Get the last seq_len days of scaled data to predict next day
            model=load_obj(model_path)
            
            input_sequence = scaled_data[-60:].copy()  # shape (seq_len, features)
            
            predictions=[]
            
            for i in range(7):
                # Reshape for prediction: (1, 60, features)
                last_sequence = input_sequence.reshape((1, 60, len(features)))

                # Predict next scaled close price
                next_day_pred_scaled = model.predict(last_sequence)[0][0]

                # Prepare array for inverse transform
                next_day_pred_full = np.zeros((1, len(features)))
                next_day_pred_full[0, 0] = next_day_pred_scaled

                # Inverse scale to get actual close price
                next_day_pred_price = self.scaler.inverse_transform(next_day_pred_full)[0, 0]

                predictions.append(round(next_day_pred_price, 2))

                # Create next input sequence: shift left, append prediction
                new_entry = np.zeros((len(features),))
                new_entry[0] = next_day_pred_scaled
                input_sequence = np.vstack([input_sequence[1:], new_entry])

            print(f"Next 7 days predictions: {predictions}")
            return predictions
        
        except Exception as e:
            raise CustomException(e, sys)
