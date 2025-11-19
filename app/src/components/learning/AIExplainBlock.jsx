import React from 'react';

export default function AIExplainBlock({ topic }) {
  return (
    <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, marginTop: 12 }}>
      <strong>Learning Mode:</strong> Explanation placeholder for <code>{topic}</code>.
    </div>
  );
}