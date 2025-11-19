import React from 'react';

export default function ConfidenceGauge({ confidence }) {
  if (confidence == null) return null;
  const pct = Math.round(confidence * 100);
  const radius = 42;
  const stroke = 8;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  return (
    <div className="bg-white rounded shadow p-3 flex flex-col items-center w-48">
      <h3 className="text-xs font-semibold mb-1">Confidence</h3>
      <svg width={110} height={110}>
        <circle cx={55} cy={55} r={radius} stroke="#e5e7eb" strokeWidth={stroke} fill="none" />
        <circle
          cx={55}
          cy={55}
          r={radius}
          stroke="#16a34a"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize="16" fontWeight="600" fill="#111827">{pct}%</text>
      </svg>
    </div>
  );
}
