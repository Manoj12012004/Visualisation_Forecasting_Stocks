import { Link, useLocation } from 'react-router-dom';
import { FaHome, FaChartLine, FaFlask, FaWallet } from 'react-icons/fa';


export default function Sidebar() {
    const r = useLocation();
    const nav = [
        { href: '/', label: 'Dashboard', icon: <FaHome /> },
        { href: '/stocks/AAPL', label: 'Stock Detail', icon: <FaChartLine /> },
        { href: '/forecast/AAPL', label: 'Forecast & Train', icon: <FaFlask /> },
        { href: '/portfolio', label: 'Portfolio', icon: <FaWallet /> },
        { href: '/backtest', label: 'Backtest Lab', icon: <FaFlask /> },
    ];

    return (
        <aside className="w-72 bg-white border-r">
            <div className="p-4 text-xl font-bold">StockLab</div>
            <nav className="p-2">
                {nav.map((n) => (
                    <Link key={n.href} to={n.href} className={`flex gap-3 items-center p-3 rounded ${r.pathname.startsWith(n.href) && n.href !== '/' ? 'bg-gray-100' : (r.pathname === n.href ? 'bg-gray-100' : 'hover:bg-gray-50')}`}>
                        <span>{n.icon}</span>
                        <span>{n.label}</span>
                    </Link>
                ))}
            </nav>
        </aside>
    );
}