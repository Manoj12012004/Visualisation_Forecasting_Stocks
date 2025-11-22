import React, { useEffect, useState } from 'react';
import Layout from '../components/core/layout';
import { useParams } from 'react-router-dom';
import ForecastConeChart from '../components/charts/ForecastConeChart';
import PredictionVsActualChart from '../components/charts/PredictionVsActualChart';
import FeatureImportanceChart from '../components/charts/FeatureImportanceChart';
import { trainStock, forecastNext, fetchFeatureImportance } from '../services/apiClient';

export default function ForecastPage() {
  const params = useParams();
  const [symbol, setSymbol] = useState(params.symbol || 'AAPL');
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [nextPred, setNextPred] = useState(null);
  const [forecastPath, setForecastPath] = useState([]);
  const [featureImp, setFeatureImp] = useState(null);

  useEffect(() => { setSymbol(params.symbol || 'AAPL'); }, [params.symbol]);

  useEffect(() => {
    let cancelled = false;
    async function loadNext() {
      try {
        const res = await forecastNext(symbol, 7);
        if (!cancelled && res?.path) {
          setForecastPath(res.path);
          if (res.path.length > 0) {
            setNextPred(res.path[0]);
          }
        }
        
        const imp = await fetchFeatureImportance(symbol);
        if (!cancelled && imp?.items) {
          setFeatureImp(imp.items);
        }
      } catch (e) {
        console.error(e);
      }
    }
    loadNext();
    return () => { cancelled = true; };
  }, [symbol, trainResult]); // Reload when training finishes

  const handleTrain = async () => {
    setTraining(true);
    setTrainResult(null);
    try {
      const res = await trainStock(symbol, true);
      const reg = res.regression_metrics || {};
      const dir = res.direction_metrics?.binary_metrics || {};
      
      setTrainResult({ 
        success: true, 
        msg: 'Model trained successfully!',
        metrics: {
          rmse: reg.rmse,
          r2: reg.r2,
          accuracy: dir.accuracy,
          precision: dir.precision
        },
        validationData: res.validation_data
      });
    } catch (e) {
      setTrainResult({ success: false, msg: 'Training failed. See console for details.' });
      console.error(e);
    } finally {
      setTraining(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Forecast & Training: {symbol}</h1>
            <p className="text-slate-500 text-sm mt-1">AI-powered market analysis and future price predictions.</p>
          </div>
          <button 
            onClick={handleTrain} 
            disabled={training}
            className={`px-4 py-2 rounded shadow-sm text-white font-medium transition-all ${training ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow'}`}
          >
            {training ? 'Training Model...' : 'Retrain Model'}
          </button>
        </div>

        {/* Training Result Notification */}
        {trainResult && (
          <div className={`p-6 rounded-lg border shadow-md ${trainResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}`}>
            <div className="flex items-center gap-2 font-semibold text-lg mb-2">
              {trainResult.success ? (
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              ) : (
                <svg className="w-6 h-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              )}
              {trainResult.msg}
            </div>
            
            {trainResult.metrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm bg-white/50 p-4 rounded border border-emerald-100">
                <div>RMSE: <span className="font-mono font-bold text-emerald-700">{trainResult.metrics.rmse?.toFixed(4) ?? 'N/A'}</span></div>
                <div>R² Score: <span className="font-mono font-bold text-emerald-700">{trainResult.metrics.r2?.toFixed(4) ?? 'N/A'}</span></div>
                <div>Dir Accuracy: <span className="font-mono font-bold text-emerald-700">{(trainResult.metrics.accuracy * 100)?.toFixed(1) ?? 'N/A'}%</span></div>
                <div>Dir Precision: <span className="font-mono font-bold text-emerald-700">{(trainResult.metrics.precision * 100)?.toFixed(1) ?? 'N/A'}%</span></div>
              </div>
            )}
            
            {trainResult.validationData && (
              <div className="mt-6 bg-white p-4 rounded border border-emerald-100 shadow-sm">
                <h3 className="font-semibold text-slate-800 mb-4">Model Validation: Predictions vs Actual (Historical)</h3>
                <PredictionVsActualChart data={trainResult.validationData} height={300} />
                <p className="text-xs text-slate-500 mt-2">
                  Comparison of model predictions against actual prices on the validation set (most recent 20% of data).
                </p>
              </div>
            )}
          </div>
        )}

        {/* Top Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Next Price Target</span>
              <div className="mt-2 flex items-baseline gap-2">
                {nextPred ? (
                  <>
                    <span className="text-4xl font-bold text-slate-900">${Number(nextPred.predicted_price).toFixed(2)}</span>
                    <span className="text-sm font-medium text-slate-400">USD</span>
                  </>
                ) : <span className="text-slate-400 italic">Loading...</span>}
              </div>
            </div>
            <div className="mt-4 text-xs text-slate-400">
              Forecast for next trading day
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Market Sentiment</span>
              <div className="mt-2">
                 {nextPred ? (
                  <div className="flex items-center gap-3">
                    <span className={`text-4xl font-bold ${Number(nextPred.probability) > 0.5 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {(Number(nextPred.probability) * 100).toFixed(1)}%
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${Number(nextPred.probability) > 0.5 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                      {Number(nextPred.probability) > 0.5 ? 'Bullish' : 'Bearish'}
                    </span>
                  </div>
                ) : <span className="text-slate-400 italic">Loading...</span>}
              </div>
            </div>
            <div className="mt-4 text-xs text-slate-400">
              Probability of price increase
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
             <div>
               <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Forecast Date</span>
               <div className="mt-2">
                  {nextPred ? (
                    <span className="text-2xl font-semibold text-slate-700">
                      {new Date(nextPred.date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                    </span>
                  ) : <span className="text-slate-400 italic">Loading...</span>}
               </div>
             </div>
             <div className="mt-4 text-xs text-slate-400">
               Valid for upcoming session
             </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column (1/2 width) */}
          <div className="space-y-8">
            {/* Forecast Cone */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="font-bold text-lg text-slate-800">7-Day Forecast Cone</h2>
                  <p className="text-sm text-slate-500">Projected price range with 90% confidence intervals</p>
                </div>
              </div>
              <ForecastConeChart symbol={symbol} days={7} height={320} />
            </div>

            {/* Feature Importance */}
            {featureImp && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="mb-6">
                  <h3 className="font-bold text-lg text-slate-800">Model Explainability</h3>
                  <p className="text-sm text-slate-500">Key indicators driving the model's prediction</p>
                </div>
                <FeatureImportanceChart data={featureImp} height={280} />
              </div>
            )}
          </div>

          {/* Right Column (1/3 width) */}
          <div className="space-y-8">
             {/* 7-Day Table */}
             {forecastPath.length > 0 && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-4">7-Day Horizon</h3>
                <div className="overflow-hidden rounded-lg border border-slate-100">
                  <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-500 font-semibold">
                      <tr>
                        <th className="px-4 py-3">Date</th>
                        <th className="px-4 py-3">Price</th>
                        <th className="px-4 py-3">Prob.</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {forecastPath.map((item) => (
                        <tr key={item.step} className="hover:bg-slate-50 transition-colors">
                          <td className="px-4 py-3 text-slate-600">
                            {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </td>
                          <td className="px-4 py-3 font-medium text-slate-900">
                            ${Number(item.predicted_price).toFixed(2)}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${Number(item.probability) > 0.5 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                              {(Number(item.probability) * 100).toFixed(0)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* About Model */}
            <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100">
              <h3 className="font-bold text-indigo-900 mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Model Architecture
              </h3>
              <p className="text-sm text-indigo-800 leading-relaxed mb-4">
                This model utilizes a hybrid LSTM (Long Short-Term Memory) neural network optimized for time-series forecasting. It processes historical price sequences alongside technical indicators to predict future trends.
              </p>
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-indigo-700 border-b border-indigo-200 pb-1">
                  <span>Update Frequency</span>
                  <span className="font-semibold">On-Demand</span>
                </div>
                <div className="flex justify-between text-xs text-indigo-700 border-b border-indigo-200 pb-1">
                  <span>Forecast Horizon</span>
                  <span className="font-semibold">7 Days</span>
                </div>
                <div className="flex justify-between text-xs text-indigo-700">
                  <span>Confidence Interval</span>
                  <span className="font-semibold">90%</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </Layout>
  );
}
