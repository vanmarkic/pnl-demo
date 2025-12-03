/**
 * StatusCard Component - Displays a metric with label.
 *
 * Learning points:
 * - React functional components with TypeScript
 * - Props typing
 * - Conditional styling
 */
import React from 'react';

interface StatusCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'green' | 'red' | 'blue' | 'default';
}

export const StatusCard: React.FC<StatusCardProps> = ({
  label,
  value,
  subValue,
  trend,
  color = 'default',
}) => {
  const colorClasses: Record<string, string> = {
    green: '#4ade80',
    red: '#ef4444',
    blue: '#60a5fa',
    default: '#a78bfa',
  };

  const trendIcons: Record<string, string> = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '12px',
        padding: '1.5rem',
        borderLeft: `4px solid ${colorClasses[color]}`,
      }}
    >
      <div style={{ color: '#888', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {typeof value === 'number' ? value.toLocaleString('en-EU', { maximumFractionDigits: 2 }) : value}
        {trend && (
          <span style={{ color: trend === 'up' ? '#4ade80' : trend === 'down' ? '#ef4444' : '#888' }}>
            {trendIcons[trend]}
          </span>
        )}
      </div>
      {subValue && (
        <div style={{ color: '#666', fontSize: '0.75rem', marginTop: '0.25rem' }}>
          {subValue}
        </div>
      )}
    </div>
  );
};
