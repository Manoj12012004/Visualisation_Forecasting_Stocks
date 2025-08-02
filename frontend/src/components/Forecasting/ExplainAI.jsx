import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList, Cell
} from "recharts";
import { Card, Typography, Tabs, Tab, Slider } from "@mui/material";

function reduceShapValues(shap3D, sampleIdx) {
  // Select one window/sample's SHAP values for display (absolute mean per feature)
  if (!Array.isArray(shap3D)) return [];
  if (shap3D?.[sampleIdx]?.[0] instanceof Array) {
    return shap3D[sampleIdx][0].map((_, featIdx) => {
      const vals = shap3D[sampleIdx].map(timestep => timestep[featIdx]);
      const meanAbs = vals.reduce((sum, val) => sum + Math.abs(val), 0) / vals.length;
      return meanAbs;
    });
  }
  return shap3D[sampleIdx] || [];
}

function makeShapBarData(shap3D, features, sampleIdx = 0, topN = 10) {
  const shapValues = reduceShapValues(shap3D, sampleIdx);
  if (!Array.isArray(shapValues)) return [];
  return features.map((name, i) => ({
    feature: name,
    shap: shapValues[i] ?? 0
  }))
  .sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap))
  .slice(0, topN);
}

function getBarColor(val) {
  if (val > 0) return "#1976d2";
  if (val < 0) return "#e53935";
  return "#aaa";
}

export default function ExplainableAI({ modelExplain }) {
  const { shap_values_seq = [], shap_values_ind = [], features = {} } = modelExplain || {};
  const feature_seq = features.sequence || [];
  const feature_ind = features.indicator || [];

  const numSamples = Math.max(shap_values_seq.length, shap_values_ind.length);
  const [tab, setTab] = useState(0);
  const [sampleIdx, setSampleIdx] = useState(0);

  const dataSeq = makeShapBarData(shap_values_seq, feature_seq, sampleIdx);
  const dataInd = makeShapBarData(shap_values_ind, feature_ind, sampleIdx);
  const currentData = tab === 0 ? dataSeq : dataInd;

  const isZero = !currentData.some(f => Math.abs(f.shap) > 1e-6);

  return (
    <Card style={{ margin: 24, padding: 24, maxWidth: 670 }}>
      <Typography variant="h6">Explainable AI – SHAP Feature Importance</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} style={{ marginBottom: 10 }}>
        <Tab label="Sequence Input" />
        <Tab label="Indicator Input" />
      </Tabs>

      <Typography variant="subtitle2" style={{marginBottom: 8}}>
        Explaining forecast at sample #{sampleIdx + 1} —
        <span style={{fontWeight:400}}> move slider to view other timesteps</span>
      </Typography>
      <Slider
        value={sampleIdx}
        min={0}
        max={numSamples > 0 ? numSamples - 1 : 0}
        onChange={(_, v) => setSampleIdx(v)}
        size="small"
        valueLabelDisplay="auto"
        style={{ marginBottom: 18, maxWidth: 320 }}
      />

      {isZero ? (
        <Typography variant="body2" color="textSecondary">
          No SHAP importance detected for this sample.
        </Typography>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            layout="vertical"
            data={currentData}
            margin={{ left: 24, right: 24, top: 10, bottom: 8 }}
          >
            <XAxis type="number" />
            <YAxis dataKey="feature" type="category" width={110} />
            <Tooltip formatter={v => typeof v === "number" ? v.toFixed(5) : "0"} />
            <Bar dataKey="shap" isAnimationActive={false}>
              {currentData.map((entry, idx) => (
                <Cell key={`cell-${idx}`} fill={getBarColor(entry.shap)} />
              ))}
              <LabelList dataKey="shap" position="right" formatter={v => v.toFixed(4)} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      <div style={{ color: "#777", fontStyle: "italic", marginTop: 7 }}>
        Blue bars: positive influence, red: negative.<br/>
        Values sorted by strength for this forecast.
      </div>
    </Card>
  );
}
