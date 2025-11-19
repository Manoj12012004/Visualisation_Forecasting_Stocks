import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { useState } from 'react';

export default function Layout({ children }) {
    const [symbol, setSymbol] = useState('AAPL');
    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col bg-gray-50">
                <TopBar symbol={symbol} onSelectSymbol={setSymbol} />
                <main className="flex-1 p-4 md:p-6">{children}</main>
            </div>
        </div>
    );
}