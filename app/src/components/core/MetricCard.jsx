export default function MetricCard({ label, value }) {
  return (
    <div className="bg-white p-4 rounded shadow min-w-[180px]">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  );
}