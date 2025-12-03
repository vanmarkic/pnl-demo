# P&L Demo - Energy Trading Risk Management

A learning demo application for understanding energy trading P&L (Profit & Loss) tracking and risk management. Built with FastAPI, React/TypeScript, SQLAlchemy, and Pandas/NumPy.

## Overview

This demo simulates the key components of an energy trading information system, covering:

- **Contract Management**: Energy supply contracts (gas, electricity)
- **Trade Execution**: Buy/sell transactions
- **P&L Tracking**: Daily profit and loss calculations
- **Risk Metrics**: VaR (Value at Risk), position delta, stress testing

## Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI | REST API framework |
| Backend | SQLAlchemy | ORM for database access |
| Backend | Pydantic | Data validation |
| Backend | Pandas/NumPy | Financial calculations |
| Frontend | React 19 | UI framework |
| Frontend | TypeScript | Type safety |
| Frontend | Recharts | Data visualization |
| Database | SQLite/PostgreSQL | Data persistence |
| DevOps | Docker | Containerization |

## Project Structure

```
pnl-demo/
├── backend/
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── contract.py  # Energy contracts
│   │   ├── trade.py     # Trade transactions
│   │   ├── position.py  # Position aggregation
│   │   ├── pnl.py       # Daily P&L records
│   │   └── price.py     # Market prices
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic layer
│   │   ├── pnl_service.py   # P&L calculations
│   │   └── risk_service.py  # VaR calculations
│   ├── routers/         # API endpoints
│   ├── utils/           # Utilities & seed data
│   └── main.py          # Application entry point
├── frontend/
│   ├── src/
│   │   ├── types/       # TypeScript interfaces
│   │   ├── api/         # API client
│   │   ├── components/  # React components
│   │   └── App.tsx      # Main application
│   └── package.json
├── docker-compose.yml   # Container orchestration
└── README.md
```

## Quick Start

### Option 1: Local Development

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Docker

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Key Concepts

### Energy Trading Domain

#### Contracts
Agreements to buy/sell energy at specified terms:
- **Forward**: Fixed price for future delivery
- **Spot**: Immediate delivery at current price
- **Swap**: Exchange fixed for floating price

#### Trades
Individual transactions within contracts:
- **BUY**: Acquire energy (long position)
- **SELL**: Deliver energy (short position)

#### P&L (Profit & Loss)
- **Realized P&L**: From settled/closed trades
- **Unrealized P&L**: Paper gain/loss on open positions
- **MTM (Mark-to-Market)**: Valuation at current prices

#### Risk Metrics
- **VaR (Value at Risk)**: Maximum expected loss at confidence level
- **Delta**: P&L sensitivity to price changes
- **Position**: Net exposure (long/short)

### Code Learning Points

#### Backend Architecture (SOLID Principles)

```python
# Single Responsibility - each service handles one domain
class ContractService:
    def create(self, contract_data): ...
    def get_by_id(self, id): ...

class PnLService:
    def calculate_daily_pnl(self, date, commodity): ...
```

#### FastAPI Dependency Injection

```python
@router.get("/contracts")
def list_contracts(db: Session = Depends(get_db)):
    service = ContractService(db)
    return service.get_all()
```

#### Pandas for Financial Calculations

```python
# P&L calculation with DataFrames
df = pd.DataFrame(trades)
buy_volume = df[df['direction'] == 'BUY']['quantity'].sum()
unrealized_pnl = ((market_price - df['price']) * df['signed_qty']).sum()
```

#### NumPy for Risk Metrics

```python
# VaR calculation
returns = np.diff(prices) / prices[:-1]
var_95 = np.percentile(returns, 5) * position_value
```

#### TypeScript Type Safety

```typescript
interface Trade {
  id: number;
  direction: 'BUY' | 'SELL';
  quantity: number;
  price: number;
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contracts` | GET, POST | Manage contracts |
| `/api/trades` | GET, POST | Manage trades |
| `/api/pnl/summary` | GET | P&L summary for date range |
| `/api/pnl/timeseries` | GET | P&L time series for charts |
| `/api/risk/dashboard` | GET | Risk metrics overview |
| `/api/risk/var/{commodity}` | GET | Calculate VaR |
| `/api/seed` | POST | Seed sample data |

## Seeding Sample Data

Click "Seed Database" in the UI or call:
```bash
curl -X POST http://localhost:8000/api/seed
```

This creates:
- 4 sample contracts (gas & electricity)
- ~11 sample trades
- 30 days of price history
- 16 days of P&L records

## Learning Exercises

1. **Add a new commodity type** (e.g., LNG)
2. **Implement trade amendments**
3. **Add real-time price updates** (WebSocket)
4. **Create position limit alerts**
5. **Add PostgreSQL support** (uncomment in docker-compose)
6. **Implement historical VaR backtesting**

## Development Tips

### Hot Reload
- Backend: `--reload` flag auto-restarts on changes
- Frontend: Vite HMR updates without refresh

### Database
- SQLite by default (development)
- PostgreSQL ready (production)
- Schema auto-creates on startup

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Related Technologies to Explore

- **Kubernetes (K8s)**: Container orchestration at scale
- **Apache Kafka**: Event streaming for trade capture
- **Redis**: Caching for market data
- **Grafana**: Monitoring and dashboards
- **AWS Athena**: Query large datasets in S3

## License

MIT - Free to use for learning purposes
