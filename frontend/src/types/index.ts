/**
 * TypeScript type definitions for the P&L Demo application.
 *
 * Learning points:
 * - TypeScript interfaces for API responses
 * - Enum-like types with string unions
 * - Optional properties with ?
 */

// Enums (as string unions for better compatibility)
export type CommodityType = 'GAS' | 'ELECTRICITY' | 'POWER';
export type ContractType = 'FORWARD' | 'SPOT' | 'SWAP' | 'OPTION';
export type TradeDirection = 'BUY' | 'SELL';
export type TradeStatus = 'PENDING' | 'CONFIRMED' | 'SETTLED' | 'CANCELLED';

// Contract types
export interface Contract {
  id: number;
  reference: string;
  name: string;
  counterparty: string;
  commodity: CommodityType;
  contract_type: ContractType;
  volume: number;
  unit_price: number;
  start_date: string;
  end_date: string;
  is_active: number;
  created_at: string;
  updated_at: string;
}

export interface ContractList {
  items: Contract[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Trade types
export interface Trade {
  id: number;
  trade_id: string;
  contract_id: number;
  direction: TradeDirection;
  quantity: number;
  price: number;
  trade_date: string;
  delivery_date: string;
  status: TradeStatus;
  trader: string | null;
  created_at: string;
  notional_value: number;
  signed_quantity: number;
}

export interface TradeList {
  items: Trade[];
  total: number;
  total_buy_volume: number;
  total_sell_volume: number;
  net_volume: number;
}

// P&L types
export interface DailyPnL {
  id: number;
  pnl_date: string;
  commodity: CommodityType;
  opening_position_value: number;
  closing_position_value: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  delta_pnl: number;
  buy_volume: number;
  sell_volume: number;
  net_volume: number;
  market_price: number | null;
  price_change: number | null;
  is_profitable: boolean;
}

export interface PnLSummary {
  start_date: string;
  end_date: string;
  commodity: CommodityType | null;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_pnl: number;
  profitable_days: number;
  loss_days: number;
  best_day_pnl: number;
  worst_day_pnl: number;
  average_daily_pnl: number;
  total_buy_volume: number;
  total_sell_volume: number;
  win_rate: number;
}

export interface PnLTimeSeries {
  dates: string[];
  realized_pnl: number[];
  unrealized_pnl: number[];
  total_pnl: number[];
  cumulative_pnl: number[];
  prices: (number | null)[];
}

// Risk types
export interface RiskMetrics {
  commodity: string;
  as_of_date: string;
  net_position: number;
  average_price: number;
  market_price: number;
  mtm_value: number;
  unrealized_pnl: number;
  delta: number;
  var_95_1d: number;
  var_99_1d: number;
  var_95_10d: number;
}

export interface RiskDashboard {
  by_commodity: RiskMetrics[];
  totals: {
    total_mtm_value: number;
    total_unrealized_pnl: number;
    total_var_95_1d: number;
  };
}

// API response types
export interface ApiHealth {
  status: string;
  service?: string;
}

export interface SeedResponse {
  message: string;
  data: {
    contracts: number;
    prices: number;
    trades: number;
    pnl_records: number;
  };
}
