import os

file_path = r"d:\AI_folder\multi-agent\dashboard\index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Insert components before AlpacaPage
components = """
        function WatchlistPage() {
            const { data, loading, error, reload } = useAsyncData(async () => {
                const [assets, watchlist] = await Promise.all([
                    fetchApi("/api/assets"),
                    fetchApi("/api/watchlist"),
                ]);
                return { assets, watchlist };
            }, []);
            
            const [toggling, setToggling] = useState({});
            
            const toggleWatchlist = async (symbol, inWatchlist) => {
                setToggling(prev => ({ ...prev, [symbol]: true }));
                try {
                    if (inWatchlist) {
                        await postApi("/api/watchlist/remove", { symbol });
                    } else {
                        await postApi("/api/watchlist/add", { symbol });
                    }
                    await reload();
                } catch (e) {
                    alert(e.message);
                } finally {
                    setToggling(prev => ({ ...prev, [symbol]: false }));
                }
            };
            
            useLucide();
            
            if (loading) return <Loading />;
            if (error) return <div className="text-red-400">Error: {error}</div>;
            
            const watchlistSymbols = new Set(data.watchlist.map(w => w.symbol));
            const assets = data.assets || [];
            
            return (
                <div className="space-y-6 fade-in">
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                            Watchlist & Universe <i data-lucide="list" className="text-primary" style={{width:20}}></i>
                        </h1>
                        <p className="text-sm text-slate-400 mt-1">Manage which assets the pipeline monitors.</p>
                    </div>
                    
                    <Card title="Asset Universe" eyebrow="Trading Pairs">
                        <Table
                            rows={assets}
                            rowKey={r => r.symbol}
                            emptyTitle="No assets found"
                            columns={[
                                { key: "symbol", label: "Symbol", render: r => <span className="font-semibold text-white">{r.symbol}</span> },
                                { key: "name", label: "Name", render: r => r.name },
                                { key: "type", label: "Type", render: r => <Badge tone={r.asset_type === "crypto" ? "amber" : "blue"}>{r.asset_type.toUpperCase()}</Badge> },
                                { key: "status", label: "Watchlist", render: r => {
                                    const inW = watchlistSymbols.has(r.symbol);
                                    return (
                                        <button 
                                            disabled={toggling[r.symbol]}
                                            onClick={() => toggleWatchlist(r.symbol, inW)}
                                            className={classNames(
                                                "px-3 py-1 rounded text-xs font-medium transition-colors",
                                                inW ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                                            )}
                                        >
                                            {toggling[r.symbol] ? "..." : (inW ? "Active" : "Add")}
                                        </button>
                                    );
                                }},
                            ]}
                        />
                    </Card>
                </div>
            );
        }

        function BacktestingPage() {
            const [symbol, setSymbol] = useState("");
            const [days, setDays] = useState(90);
            const [holdDays, setHoldDays] = useState(3);
            const [result, setResult] = useState(null);
            const [running, setRunning] = useState(false);
            const [error, setError] = useState("");
            useLucide();
            
            const runBacktest = async (e) => {
                e.preventDefault();
                if (!symbol) return;
                setRunning(true);
                setError("");
                setResult(null);
                
                try {
                    const res = await postApi(`/api/backtest/${symbol}?days=${days}&hold_days=${holdDays}`);
                    if (res.status === "error") {
                        setError(res.reason);
                        setRunning(false);
                        return;
                    }
                    
                    // Start polling
                    const poll = setInterval(async () => {
                        try {
                            const check = await fetchApi(`/api/backtest/${symbol}?days=${days}&hold_days=${holdDays}`);
                            if (check.status !== "running") {
                                clearInterval(poll);
                                setRunning(false);
                                if (check.status === "error") {
                                    setError(check.reason);
                                } else {
                                    setResult(check);
                                }
                            }
                        } catch (err) {
                            clearInterval(poll);
                            setRunning(false);
                            setError("Polling error: " + err.message);
                        }
                    }, 2000);
                } catch(err) {
                    setError("Failed to start backtest: " + err.message);
                    setRunning(false);
                }
            };
            
            return (
                <div className="max-w-3xl space-y-6 fade-in">
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                            Backtesting <i data-lucide="line-chart" className="text-primary" style={{width:20}}></i>
                        </h1>
                        <p className="text-sm text-slate-400 mt-1">Evaluate strategy performance on historical data.</p>
                    </div>
                    
                    <Card title="Configure Run">
                        <form onSubmit={runBacktest} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <Field label="Symbol" type="text" value={symbol} onChange={setSymbol} placeholder="e.g. BTC" />
                                <Field label="Lookback Days" type="number" value={days} onChange={setDays} />
                                <Field label="Hold Days" type="number" value={holdDays} onChange={setHoldDays} />
                            </div>
                            <div className="flex justify-end pt-2">
                                <Button tone="primary" type="submit" icon="play" disabled={running || !symbol}>
                                    {running ? "Running..." : "Run Backtest"}
                                </Button>
                            </div>
                            {error && <div className="text-red-400 text-sm">{error}</div>}
                        </form>
                    </Card>
                    
                    {running && (
                        <Card>
                            <div className="py-12 flex flex-col items-center justify-center text-slate-400">
                                <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                                Running historical simulation for {symbol.toUpperCase()}...
                            </div>
                        </Card>
                    )}
                    
                    {result && result.status !== "error" && result.status !== "not_run" && (
                        <Card title="Results" eyebrow={result.symbol}>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                <Metric label="Accuracy" value={(result.win_rate * 100).toFixed(1) + "%"} tone="green" />
                                <Metric label="Total Signals" value={result.total_signals} />
                                <Metric label="Total P/L" value={(result.total_pnl_pct).toFixed(2) + "%"} tone={result.total_pnl_pct >= 0 ? "green" : "red"} />
                                <Metric label="Avg Return/Trade" value={(result.avg_pnl_pct).toFixed(2) + "%"} />
                            </div>
                        </Card>
                    )}
                </div>
            );
        }

        function AlpacaPage() {
"""
if "function AlpacaPage() {" in content and "function WatchlistPage() {" not in content:
    content = content.replace("        function AlpacaPage() {", components)

# 2. Update navItems
nav_old = """            const navItems = [
                { id: "overview", label: "Overview", icon: "layout-dashboard" },
                { id: "simulator", label: "Simulator", icon: "wallet" },
                { id: "alpaca", label: "Alpaca Broker", icon: "line-chart" },
                { id: "logs", label: "Live Terminal", icon: "terminal" },
                { id: "settings", label: "Settings", icon: "settings" },
                { id: "advisor", label: "AI Advisor", icon: "bot" },
            ];"""
nav_new = """            const navItems = [
                { id: "overview", label: "Overview", icon: "layout-dashboard" },
                { id: "simulator", label: "Simulator", icon: "wallet" },
                { id: "alpaca", label: "Alpaca Broker", icon: "bar-chart-2" },
                { id: "watchlist", label: "Watchlist", icon: "list" },
                { id: "backtest", label: "Backtesting", icon: "line-chart" },
                { id: "logs", label: "Live Terminal", icon: "terminal" },
                { id: "settings", label: "Settings", icon: "settings" },
                { id: "advisor", label: "AI Advisor", icon: "bot" },
            ];"""

if nav_old in content:
    content = content.replace(nav_old, nav_new)
elif nav_old.replace('\\n', '\\r\\n') in content:
    content = content.replace(nav_old.replace('\\n', '\\r\\n'), nav_new)

# 3. Update router
router_old = """                            {page === "simulator" && <SimulatorPage />}
                            {page === "alpaca" && <AlpacaPage />}
                            {page === "logs" && <LogsPage />}"""
router_new = """                            {page === "simulator" && <SimulatorPage />}
                            {page === "alpaca" && <AlpacaPage />}
                            {page === "watchlist" && <WatchlistPage />}
                            {page === "backtest" && <BacktestingPage />}
                            {page === "logs" && <LogsPage />}"""

if router_old in content:
    content = content.replace(router_old, router_new)
elif router_old.replace('\\n', '\\r\\n') in content:
    content = content.replace(router_old.replace('\\n', '\\r\\n'), router_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Pages patched successfully.")
