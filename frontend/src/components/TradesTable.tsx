/**
 * TradesTable Component - Displays trades list.
 *
 * Learning points:
 * - Conditional rendering
 * - Direction-based styling (BUY = green, SELL = red)
 */
import React from 'react';
import type { Trade } from '../types';

interface TradesTableProps {
  trades: Trade[];
  loading: boolean;
  summary?: {
    total_buy_volume: number;
    total_sell_volume: number;
    net_volume: number;
  };
}

export const TradesTable: React.FC<TradesTableProps> = ({ trades, loading, summary }) => {
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading trades...</div>;
  }

  if (trades.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        No trades found. Seed the database to create sample data.
      </div>
    );
  }

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div>
      {summary && (
        <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
          <div>
            <span style={{ color: '#888', fontSize: '0.75rem' }}>Buy Volume</span>
            <div style={{ color: '#4ade80', fontWeight: 'bold' }}>
              {summary.total_buy_volume.toLocaleString()} MWh
            </div>
          </div>
          <div>
            <span style={{ color: '#888', fontSize: '0.75rem' }}>Sell Volume</span>
            <div style={{ color: '#ef4444', fontWeight: 'bold' }}>
              {summary.total_sell_volume.toLocaleString()} MWh
            </div>
          </div>
          <div>
            <span style={{ color: '#888', fontSize: '0.75rem' }}>Net Position</span>
            <div style={{ color: summary.net_volume >= 0 ? '#4ade80' : '#ef4444', fontWeight: 'bold' }}>
              {summary.net_volume >= 0 ? '+' : ''}{summary.net_volume.toLocaleString()} MWh
            </div>
          </div>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #333' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Trade ID</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', color: '#888' }}>Direction</th>
              <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Quantity</th>
              <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Price</th>
              <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Notional</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Trade Date</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Status</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Trader</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <tr key={trade.id} style={{ borderBottom: '1px solid #333' }}>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {trade.trade_id}
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '2px 12px',
                      borderRadius: '4px',
                      backgroundColor: trade.direction === 'BUY' ? 'rgba(74, 222, 128, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: trade.direction === 'BUY' ? '#4ade80' : '#ef4444',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                    }}
                  >
                    {trade.direction}
                  </span>
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                  {trade.quantity.toLocaleString()} MWh
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                  €{trade.price.toFixed(2)}
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 'bold' }}>
                  €{trade.notional_value.toLocaleString()}
                </td>
                <td style={{ padding: '12px 8px', fontSize: '0.75rem' }}>
                  {formatDateTime(trade.trade_date)}
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: trade.status === 'CONFIRMED' ? 'rgba(74, 222, 128, 0.2)' :
                                      trade.status === 'PENDING' ? 'rgba(251, 191, 36, 0.2)' :
                                      'rgba(107, 114, 128, 0.2)',
                      color: trade.status === 'CONFIRMED' ? '#4ade80' :
                             trade.status === 'PENDING' ? '#fbbf24' : '#888',
                    }}
                  >
                    {trade.status}
                  </span>
                </td>
                <td style={{ padding: '12px 8px', color: '#888' }}>
                  {trade.trader || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
