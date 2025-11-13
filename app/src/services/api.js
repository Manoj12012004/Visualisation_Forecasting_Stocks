import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/', // change if backend runs on a different port
});

export const trainModel=(symbol)=>{
  api.get(`/stocks/${symbol}/train_cnn_two_stage`);
}

export const getSignals=(symbol)=>{
  api.get(`/stocks/${symbol}/signals`);
}

export const getSimulation=(symbol)=>{
  api.get(`/stocks/${symbol}/simulate`);
}

export const getMetrics=(symbol)=>{
  api.get(`/stocks/${symbol}/metrics`);
}

export const getExplain=(symbol)=>{
  api.get(`/stocks/${symbol}/explain`);
}

export const getVisualisation=(symbol)=>{
  api.get(`/stocks/${symbol}/visualise`);
}


