/**
 * RiskPanel Component - Displays risk metrics.
 *
 * Learning points:
 * - Risk visualization
 * - VaR display
 * - Color coding for risk levels
 */
import React from 'react';
import type { RiskDashboard } from '../types';

interface RiskPanelProps {
  data: RiskDashboard | null;
  loading: boolean;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({ data, loading }) => {
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading risk metrics...</div>;
  }

  if (!data) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        No risk data available.
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const commodityColors: Record<string, string> = {
    GAS: '#f59e0b',
    ELECTRICITY: '#3b82f6',
  };

  return (
    <div>
      {/* Totals summary */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1rem',
          marginBottom: '1.5rem',
          padding: '1rem',
          background: 'rgba(255,255,255,0.02)',
          borderRadius: '8px',
        }}
      >
        <div>
          <div style={{ color: '#888', fontSize: '0.75rem' }}>Total MTM Value</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
            {formatCurrency(data.totals.total_mtm_value)}
          </div>
        </div>
        <div>
          <div style={{ color: '#888', fontSize: '0.75rem' }}>Total Unrealized P&L</div>
          <div
            style={{
              fontSize: '1.25rem',
              fontWeight: 'bold',
              color: data.totals.total_unrealized_pnl >= 0 ? '#4ade80' : '#ef4444',
            }}
          >
            {data.totals.total_unrealized_pnl >= 0 ? '+' : ''}
            {formatCurrency(data.totals.total_unrealized_pnl)}
          </div>
        </div>
        <div>
          <div style={{ color: '#888', fontSize: '0.75rem' }}>Total VaR (95%, 1-day)</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#ef4444' }}>
            {formatCurrency(data.totals.total_var_95_1d)}
          </div>
        </div>
      </div>

      {/* Per-commodity breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
        {data.by_commodity.map((metrics) => (
          <div
            key={metrics.commodity}
            style={{
              padding: '1rem',
              background: 'rgba(255,255,255,0.03)',
              borderRadius: '8px',
              borderLeft: `4px solid ${commodityColors[metrics.commodity] || '#888'}`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <span
                style={{
                  fontSize: '1rem',
                  fontWeight: 'bold',
                  color: commodityColors[metrics.commodity],
                }}
              >
                {metrics.commodity}
              </span>
              <span style={{ fontSize: '0.75rem', color: '#888' }}>
                {metrics.as_of_date}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.875rem' }}>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>Net Position</div>
                <div style={{ fontWeight: '500' }}>
                  {metrics.net_position.toLocaleString()} MWh
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>Market Price</div>
                <div style={{ fontWeight: '500' }}>€{metrics.market_price}</div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>MTM Value</div>
                <div style={{ fontWeight: '500' }}>{formatCurrency(metrics.mtm_value)}</div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>Unrealized P&L</div>
                <div
                  style={{
                    fontWeight: '500',
                    color: metrics.unrealized_pnl >= 0 ? '#4ade80' : '#ef4444',
                  }}
                >
                  {metrics.unrealized_pnl >= 0 ? '+' : ''}
                  {formatCurrency(metrics.unrealized_pnl)}
                </div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>Delta</div>
                <div style={{ fontWeight: '500' }}>{metrics.delta.toLocaleString()}</div>
              </div>
              <div>
                <div style={{ color: '#666', fontSize: '0.7rem' }}>VaR 95% (1d)</div>
                <div style={{ fontWeight: '500', color: '#f59e0b' }}>
                  {formatCurrency(metrics.var_95_1d)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
