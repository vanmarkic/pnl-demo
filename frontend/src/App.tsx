/**
 * Main App Component - P&L Dashboard
 *
 * Learning points:
 * - React hooks (useState, useEffect, useCallback)
 * - State management
 * - Tab-based navigation
 * - API integration
 */
import { useState, useEffect, useCallback } from 'react';
import { api } from './api/client';
import { StatusCard } from './components/StatusCard';
import { PnLChart } from './components/PnLChart';
import { ContractsTable } from './components/ContractsTable';
import { TradesTable } from './components/TradesTable';
import { RiskPanel } from './components/RiskPanel';
import type { Contract, Trade, PnLSummary, PnLTimeSeries, RiskDashboard } from './types';
import './App.css';

type TabType = 'dashboard' | 'contracts' | 'trades' | 'risk';

function App() {
  // API connection state
  const [apiStatus, setApiStatus] = useState<string>('checking...');
  const [seeding, setSeeding] = useState(false);

  // Active tab
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  // Data states
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [tradeSummary, setTradeSummary] = useState<{ total_buy_volume: number; total_sell_volume: number; net_volume: number } | undefined>();
  const [pnlSummary, setPnlSummary] = useState<PnLSummary | null>(null);
  const [pnlTimeSeries, setPnlTimeSeries] = useState<PnLTimeSeries | null>(null);
  const [riskData, setRiskData] = useState<RiskDashboard | null>(null);

  // Loading states
  const [loading, setLoading] = useState({
    contracts: true,
    trades: true,
    pnl: true,
    risk: true,
  });

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Get date range for P&L (last 30 days)
  const getDateRange = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    };
  };

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      // Check API health first
      const health = await api.health();
      setApiStatus(health.status);

      // Fetch all data in parallel
      const { start, end } = getDateRange();

      const [contractsRes, tradesRes, pnlSummaryRes, pnlTimeSeriesRes, riskRes] = await Promise.allSettled([
        api.contracts.list(1, 20),
        api.trades.list(1, 50),
        api.pnl.getSummary(start, end),
        api.pnl.getTimeSeries(start, end),
        api.risk.getDashboard(),
      ]);

      // Process results
      if (contractsRes.status === 'fulfilled') {
        setContracts(contractsRes.value.items);
      }
      setLoading(prev => ({ ...prev, contracts: false }));

      if (tradesRes.status === 'fulfilled') {
        setTrades(tradesRes.value.items);
        setTradeSummary({
          total_buy_volume: tradesRes.value.total_buy_volume,
          total_sell_volume: tradesRes.value.total_sell_volume,
          net_volume: tradesRes.value.net_volume,
        });
      }
      setLoading(prev => ({ ...prev, trades: false }));

      if (pnlSummaryRes.status === 'fulfilled') {
        setPnlSummary(pnlSummaryRes.value);
      }
      if (pnlTimeSeriesRes.status === 'fulfilled') {
        setPnlTimeSeries(pnlTimeSeriesRes.value);
      }
      setLoading(prev => ({ ...prev, pnl: false }));

      if (riskRes.status === 'fulfilled') {
        setRiskData(riskRes.value);
      }
      setLoading(prev => ({ ...prev, risk: false }));

    } catch (err) {
      setApiStatus('disconnected');
      setError(err instanceof Error ? err.message : 'Failed to connect to API');
      setLoading({ contracts: false, trades: false, pnl: false, risk: false });
    }
  }, []);

  // Seed database
  const handleSeed = async () => {
    setSeeding(true);
    setError(null);
    try {
      await api.seed();
      // Refresh data after seeding
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to seed database');
    } finally {
      setSeeding(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div>
            {/* KPI Cards */}
            <div className="kpi-grid">
              <StatusCard
                label="Total P&L (30 days)"
                value={pnlSummary ? `€${pnlSummary.total_pnl.toLocaleString()}` : '—'}
                trend={pnlSummary && pnlSummary.total_pnl > 0 ? 'up' : pnlSummary && pnlSummary.total_pnl < 0 ? 'down' : 'neutral'}
                color={pnlSummary && pnlSummary.total_pnl >= 0 ? 'green' : 'red'}
              />
              <StatusCard
                label="Win Rate"
                value={pnlSummary ? `${pnlSummary.win_rate.toFixed(1)}%` : '—'}
                subValue={pnlSummary ? `${pnlSummary.profitable_days} profitable / ${pnlSummary.loss_days} loss days` : undefined}
                color="blue"
              />
              <StatusCard
                label="Active Contracts"
                value={contracts.length}
                color="default"
              />
              <StatusCard
                label="Total Trades"
                value={trades.length}
                subValue={tradeSummary ? `Net: ${tradeSummary.net_volume.toLocaleString()} MWh` : undefined}
                color="default"
              />
            </div>

            {/* P&L Chart */}
            <div className="section">
              <h3>P&L Performance (Last 30 Days)</h3>
              <PnLChart data={pnlTimeSeries} loading={loading.pnl} />
            </div>

            {/* Risk Summary */}
            <div className="section">
              <h3>Risk Overview</h3>
              <RiskPanel data={riskData} loading={loading.risk} />
            </div>
          </div>
        );

      case 'contracts':
        return (
          <div className="section">
            <h3>Energy Contracts</h3>
            <ContractsTable contracts={contracts} loading={loading.contracts} />
          </div>
        );

      case 'trades':
        return (
          <div className="section">
            <h3>Trade Blotter</h3>
            <TradesTable trades={trades} loading={loading.trades} summary={tradeSummary} />
          </div>
        );

      case 'risk':
        return (
          <div className="section">
            <h3>Risk Management</h3>
            <RiskPanel data={riskData} loading={loading.risk} />

            {/* VaR Explanation */}
            <div className="info-box">
              <h4>Understanding VaR (Value at Risk)</h4>
              <p>
                VaR is a statistical measure that quantifies the potential loss in value of a portfolio
                over a defined period for a given confidence interval.
              </p>
              <ul>
                <li><strong>VaR 95% (1-day)</strong>: Maximum expected loss over 1 day with 95% confidence</li>
                <li><strong>VaR 99% (1-day)</strong>: Maximum expected loss over 1 day with 99% confidence</li>
                <li><strong>VaR 95% (10-day)</strong>: Maximum expected loss over 10 days with 95% confidence</li>
              </ul>
              <p style={{ color: '#888', fontSize: '0.875rem' }}>
                Example: VaR 95% = €10,000 means we are 95% confident that our loss will not exceed €10,000.
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>P&L Demo</h1>
          <span className="subtitle">Energy Trading Risk Management</span>
        </div>
        <div className="header-actions">
          <span className={`status-badge ${apiStatus === 'healthy' ? 'connected' : 'disconnected'}`}>
            API: {apiStatus}
          </span>
          <button
            onClick={handleSeed}
            disabled={seeding || apiStatus !== 'healthy'}
            className="seed-button"
          >
            {seeding ? 'Seeding...' : 'Seed Database'}
          </button>
        </div>
      </header>

      {/* Error message */}
      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Navigation tabs */}
      <nav className="tabs">
        {(['dashboard', 'contracts', 'trades', 'risk'] as TabType[]).map((tab) => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </nav>

      {/* Main content */}
      <main className="main-content">
        {renderTabContent()}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          Built with React + TypeScript | FastAPI | SQLAlchemy | Pandas
        </p>
        <p style={{ fontSize: '0.75rem', color: '#666' }}>
          Learning Demo for Energy Trading P&L and Risk Management
        </p>
      </footer>
    </div>
  );
}

export default App;
