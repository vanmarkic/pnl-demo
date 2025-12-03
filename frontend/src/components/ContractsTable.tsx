/**
 * ContractsTable Component - Displays contracts list.
 *
 * Learning points:
 * - Table rendering in React
 * - Date formatting
 * - Status badges
 */
import React from 'react';
import type { Contract } from '../types';

interface ContractsTableProps {
  contracts: Contract[];
  loading: boolean;
}

export const ContractsTable: React.FC<ContractsTableProps> = ({ contracts, loading }) => {
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading contracts...</div>;
  }

  if (contracts.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        No contracts found. Seed the database to create sample data.
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

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
    POWER: '#8b5cf6',
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #333' }}>
            <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Reference</th>
            <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Name</th>
            <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Commodity</th>
            <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Type</th>
            <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Volume (MWh)</th>
            <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Price</th>
            <th style={{ padding: '12px 8px', textAlign: 'right', color: '#888' }}>Notional</th>
            <th style={{ padding: '12px 8px', textAlign: 'left', color: '#888' }}>Period</th>
          </tr>
        </thead>
        <tbody>
          {contracts.map((contract) => (
            <tr key={contract.id} style={{ borderBottom: '1px solid #333' }}>
              <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>{contract.reference}</td>
              <td style={{ padding: '12px 8px' }}>{contract.name}</td>
              <td style={{ padding: '12px 8px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: commodityColors[contract.commodity] + '20',
                    color: commodityColors[contract.commodity],
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                  }}
                >
                  {contract.commodity}
                </span>
              </td>
              <td style={{ padding: '12px 8px', color: '#888' }}>{contract.contract_type}</td>
              <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                {contract.volume.toLocaleString()}
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                €{contract.unit_price.toFixed(2)}
              </td>
              <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 'bold' }}>
                {formatCurrency(contract.volume * contract.unit_price)}
              </td>
              <td style={{ padding: '12px 8px', fontSize: '0.75rem', color: '#888' }}>
                {formatDate(contract.start_date)} - {formatDate(contract.end_date)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
