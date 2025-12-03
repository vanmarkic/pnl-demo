/**
 * API Client - Centralized API communication.
 *
 * Learning points:
 * - Fetch API with TypeScript
 * - Generic request function
 * - Error handling
 */
import type {
  ContractList,
  TradeList,
  PnLSummary,
  PnLTimeSeries,
  RiskDashboard,
  RiskMetrics,
  ApiHealth,
  SeedResponse,
  CommodityType,
} from '../types';

const API_URL = 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * API client with typed methods.
 */
export const api = {
  // Health check
  health: () => request<ApiHealth>('/health'),

  // Seed database
  seed: () => request<SeedResponse>('/api/seed', { method: 'POST' }),

  // Contracts
  contracts: {
    list: (page = 1, size = 10) =>
      request<ContractList>(`/api/contracts?page=${page}&size=${size}`),

    getVolumeSummary: () =>
      request<Record<string, number>>('/api/contracts/volume-summary'),
  },

  // Trades
  trades: {
    list: (page = 1, size = 20) =>
      request<TradeList>(`/api/trades?page=${page}&size=${size}`),

    getSummary: () =>
      request<{
        total_buy_volume: number;
        total_sell_volume: number;
        net_volume: number;
        buy_count: number;
        sell_count: number;
      }>('/api/trades/summary'),
  },

  // P&L
  pnl: {
    getSummary: (startDate: string, endDate: string, commodity?: CommodityType) => {
      let url = `/api/pnl/summary?start_date=${startDate}&end_date=${endDate}`;
      if (commodity) url += `&commodity=${commodity}`;
      return request<PnLSummary>(url);
    },

    getTimeSeries: (startDate: string, endDate: string, commodity?: CommodityType) => {
      let url = `/api/pnl/timeseries?start_date=${startDate}&end_date=${endDate}`;
      if (commodity) url += `&commodity=${commodity}`;
      return request<PnLTimeSeries>(url);
    },

    getMTD: (commodity?: CommodityType) => {
      let url = '/api/pnl/mtd';
      if (commodity) url += `?commodity=${commodity}`;
      return request<PnLSummary>(url);
    },

    getYTD: (commodity?: CommodityType) => {
      let url = '/api/pnl/ytd';
      if (commodity) url += `?commodity=${commodity}`;
      return request<PnLSummary>(url);
    },
  },

  // Risk
  risk: {
    getDashboard: () => request<RiskDashboard>('/api/risk/dashboard'),

    getMetrics: (commodity: CommodityType) =>
      request<RiskMetrics>(`/api/risk/metrics/${commodity}`),

    stressTest: (commodity: CommodityType, priceShockPct: number) =>
      request<{
        commodity: string;
        current_price: number;
        price_shock_pct: number;
        shocked_price: number;
        net_position: number;
        pnl_impact: number;
        interpretation: string;
      }>(`/api/risk/stress-test/${commodity}?price_shock_pct=${priceShockPct}`),
  },
};
