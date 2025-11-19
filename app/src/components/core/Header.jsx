export default function Header({ children, right }) {
  return (
    <div className="flex items-center justify-between mb-6">
    <div>{children}</div>
    <div>{right}</div>
    </div>
  );
}