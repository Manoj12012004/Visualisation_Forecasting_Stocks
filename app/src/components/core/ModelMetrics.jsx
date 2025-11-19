import { useEffect, useState, useCallback } from 'react';
import { fetchMetrics, evaluatePredictions } from '../../services/apiClient';

export default function ModelMetrics({ symbol }) {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!symbol) return;
    setLoading(true);
    setErr(null);
    try {
      const m = await fetchMetrics(symbol);
      setMetrics(m);
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => { load(); }, [load]);

  async function onEvaluate() {
    if (!symbol) return;
    setBusy(true);
    try {
      await evaluatePredictions(symbol);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-white rounded shadow p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">Model Metrics</h3>
        <div className="flex gap-2">
          <button onClick={load} disabled={loading} className="text-xs bg-slate-200 hover:bg-slate-300 px-2 py-1 rounded">{loading ? 'Loading...' : 'Refresh'}</button>
          <button onClick={onEvaluate} disabled={busy} className="text-xs bg-indigo-600 text-white px-2 py-1 rounded">{busy ? 'Evaluating...' : 'Evaluate'}</button>
        </div>
      </div>

      {err && <div className="text-xs text-red-600 mb-2">{String(err)}</div>}
      {!metrics && !loading && !err && <div className="text-xs text-slate-600">No data yet.</div>}

      {metrics && metrics.message && (
        <div className="text-xs text-slate-600">{metrics.message}</div>
      )}

      {metrics && !metrics.message && (
        <div className="space-y-3">
          <div className="grid grid-cols-4 gap-2 text-xs">
            <Metric label="Accuracy" value={pct(metrics.classification?.accuracy)} />
            <Metric label="Precision" value={pct(metrics.classification?.precision)} />
            <Metric label="Recall" value={pct(metrics.classification?.recall)} />
            <Metric label="F1" value={pct(metrics.classification?.f1)} />
          </div>

          <div>
            <div className="text-xs font-medium mb-1">Confusion Matrix</div>
            <table className="w-full text-xs text-center border-collapse">
              <tbody>
                <tr>
                  <td className="border p-1 bg-slate-50"></td>
                  <td className="border p-1 bg-slate-50">Actual Up</td>
                  <td className="border p-1 bg-slate-50">Actual Down</td>
                </tr>
                <tr>
                  <td className="border p-1 bg-slate-50">Pred Up</td>
                  <td className="border p-1">{metrics.classification?.confusion_matrix?.tp ?? '-'}</td>
                  <td className="border p-1">{metrics.classification?.confusion_matrix?.fp ?? '-'}</td>
                </tr>
                <tr>
                  <td className="border p-1 bg-slate-50">Pred Down</td>
                  <td className="border p-1">{metrics.classification?.confusion_matrix?.fn ?? '-'}</td>
                  <td className="border p-1">{metrics.classification?.confusion_matrix?.tn ?? '-'}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs">
            <Metric label="RMSE" value={fmt(metrics.regression?.rmse)} />
            <Metric label="R²" value={fmt(metrics.regression?.r2)} />
            <Metric label="MAPE" value={fmt(metrics.regression?.mape)} suffix="%" />
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, suffix }) {
  return (
    <div className="bg-slate-50 rounded p-2 text-center">
      <div className="text-[11px] text-slate-600">{label}</div>
      <div className="text-sm font-semibold">{value != null ? `${value}${suffix || ''}` : '-'}</div>
    </div>
  );
}

function pct(v){
  if (v == null) return null;
  return (Math.round(v * 10000) / 100).toFixed(2) + '%';
}
function fmt(v){
  if (v == null) return null;
  const n = Number(v);
  if (!isFinite(n)) return String(v);
  return Math.abs(n) >= 1 ? n.toFixed(3) : n.toExponential(2);
}
