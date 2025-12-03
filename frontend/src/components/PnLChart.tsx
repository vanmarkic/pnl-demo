/**
 * PnLChart Component - Displays P&L time series chart.
 *
 * Learning points:
 * - Using Recharts library
 * - Responsive charts
 * - Custom tooltips
 */
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import type { PnLTimeSeries } from '../types';

interface PnLChartProps {
  data: PnLTimeSeries | null;
  loading: boolean;
}

export const PnLChart: React.FC<PnLChartProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading chart...
      </div>
    );
  }

  if (!data || data.dates.length === 0) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
        No P&L data available. Click "Seed Database" to generate sample data.
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = data.dates.map((date, i) => ({
    date: new Date(date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    realized: data.realized_pnl[i],
    unrealized: data.unrealized_pnl[i],
    total: data.total_pnl[i],
    cumulative: data.cumulative_pnl[i],
  }));

  return (
    <div style={{ width: '100%', height: 350 }}>
      <ResponsiveContainer>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="date"
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
          />
          <YAxis
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
            tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [`€${value.toLocaleString()}`, '']}
            labelStyle={{ color: '#888' }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="cumulative"
            fill="rgba(96, 165, 250, 0.2)"
            stroke="#60a5fa"
            strokeWidth={2}
            name="Cumulative P&L"
          />
          <Line
            type="monotone"
            dataKey="total"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={false}
            name="Daily P&L"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
