import React, { useEffect, useMemo, useState } from 'react';
import Layout from '../components/core/layout';
import MarketSnapshot from '../components/dashboard/MarketSnapshot';
import PredictionCard from '../components/Cards/PredictionCard';
import WatchlistTable from '../components/Tables/WatchlistTable';
import { fetchHeatmap } from '../services/apiClient';

export default function Home() {
	return (
		<Layout>
			<div className="space-y-4">
				<TickerTape />
				<div className="grid lg:grid-cols-3 gap-4">
					<div className="lg:col-span-2 space-y-4">
						<MarketSnapshot />
					</div>
					<div className="space-y-4">
						<PredictionCard />
						<TopMovers />
					</div>
				</div>
				<WatchlistTable />
			</div>
		</Layout>
	);
}

function TickerTape() {
	const [rows, setRows] = useState([]);
	useEffect(() => {
		fetchHeatmap(['^GSPC','^IXIC','^NSEI']).then(setRows).catch(()=>setRows([]));
	}, []);
	return (
		<div className="bg-white border rounded p-2 overflow-hidden">
			<div className="flex gap-6 whitespace-nowrap">
				{rows.map((r,i)=> (
					<div key={i} className="text-sm">
						<span className="font-semibold mr-2">{r.symbol}</span>
						<span className={`${(r.pct_change||0)>=0?'text-emerald-600':'text-rose-600'}`}>{(r.pct_change||0).toFixed(2)}%</span>
					</div>
				))}
			</div>
		</div>
	);
}

function TopMovers() {
	const [data, setData] = useState([]);
	useEffect(() => { fetchHeatmap().then(setData).catch(()=>setData([])); }, []);
	const gainers = useMemo(()=> [...data].sort((a,b)=>(b.pct_change||0)-(a.pct_change||0)).slice(0,3), [data]);
	const losers = useMemo(()=> [...data].sort((a,b)=>(a.pct_change||0)-(b.pct_change||0)).slice(0,3), [data]);
	return (
		<div className="bg-white rounded border p-4">
			<div className="font-semibold mb-2">Top Movers</div>
			<div className="grid grid-cols-2 gap-4 text-sm">
				<div>
					<div className="text-xs text-slate-500 mb-1">Gainers</div>
					{gainers.map((x,i)=>(
						<div key={i} className="flex justify-between py-1 border-b">
							<span>{x.symbol}</span><span className="text-emerald-600">{(x.pct_change||0).toFixed(2)}%</span>
						</div>
					))}
				</div>
				<div>
					<div className="text-xs text-slate-500 mb-1">Losers</div>
					{losers.map((x,i)=>(
						<div key={i} className="flex justify-between py-1 border-b">
							<span>{x.symbol}</span><span className="text-rose-600">{(x.pct_change||0).toFixed(2)}%</span>
						</div>
					))}
				</div>
			</div>
		</div>
	);
}