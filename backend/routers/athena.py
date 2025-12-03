"""
Athena API Router - SQL queries on S3 data

Learning points:
- Running SQL on S3 data without ETL
- Serverless analytics
- Cost-effective big data queries
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from typing import Optional

from services.athena_service import get_athena_service, AthenaService
from models.contract import CommodityType

router = APIRouter(
    prefix="/api/athena",
    tags=["athena"],
    responses={404: {"description": "Not found"}},
)


def get_athena() -> AthenaService:
    """Dependency for Athena service."""
    return get_athena_service()


@router.post("/setup")
async def setup_athena(athena: AthenaService = Depends(get_athena)):
    """
    Initialize Athena database and tables.

    Run this once to set up Athena for querying S3 data.

    Creates:
    - pnl_demo_db database
    - prices table (external, points to S3)
    - trades table (external, points to S3)
    """
    results = {
        "database": athena.create_database(),
        "prices_table": athena.create_prices_table(),
        "trades_table": athena.create_trades_table(),
    }

    success = all(results.values())
    return {
        "message": "Athena setup complete" if success else "Athena setup had errors",
        "results": results
    }


@router.post("/query")
async def run_query(
    query: str,
    timeout: int = Query(300, ge=10, le=600),
    athena: AthenaService = Depends(get_athena)
):
    """
    Execute a custom Athena SQL query.

    Example queries:
    ```sql
    -- Get all gas prices
    SELECT * FROM pnl_demo_db.prices WHERE commodity = 'GAS' LIMIT 100

    -- Price statistics
    SELECT commodity, AVG(price), MIN(price), MAX(price)
    FROM pnl_demo_db.prices
    GROUP BY commodity

    -- Daily returns
    SELECT price_date, price,
           LAG(price) OVER (ORDER BY price_date) as prev_price
    FROM pnl_demo_db.prices
    WHERE commodity = 'ELECTRICITY'
    ```

    **Note**: Athena charges ~$5 per TB of data scanned.
    """
    # Basic SQL injection prevention (Athena has its own protections too)
    forbidden = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'INSERT', 'UPDATE']
    query_upper = query.upper()
    for word in forbidden:
        if word in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains forbidden keyword: {word}"
            )

    df = athena.execute_query(query, timeout)

    if df is None:
        raise HTTPException(
            status_code=500,
            detail="Query execution failed"
        )

    return {
        "columns": list(df.columns),
        "data": df.to_dict(orient="records"),
        "row_count": len(df)
    }


@router.get("/prices/history")
async def get_price_history(
    commodity: CommodityType,
    start_date: date,
    end_date: date,
    athena: AthenaService = Depends(get_athena)
):
    """
    Get historical price data from S3 via Athena.

    This queries the prices table which points to S3 data.
    Much faster than database for large historical datasets.
    """
    df = athena.get_price_history(
        commodity.value,
        start_date.isoformat(),
        end_date.isoformat()
    )

    if df is None:
        raise HTTPException(status_code=500, detail="Query failed")

    return {
        "commodity": commodity.value,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data": df.to_dict(orient="records"),
        "row_count": len(df)
    }


@router.get("/prices/statistics")
async def get_price_statistics(
    commodity: CommodityType,
    year: int = Query(..., ge=2020, le=2030),
    athena: AthenaService = Depends(get_athena)
):
    """
    Get price statistics aggregated by Athena.

    Returns:
    - Min/Max/Avg price
    - Price volatility (standard deviation)
    - Median price
    - Data point count
    """
    df = athena.get_price_statistics(commodity.value, year)

    if df is None or len(df) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {commodity.value} in {year}"
        )

    return {
        "commodity": commodity.value,
        "year": year,
        "statistics": df.to_dict(orient="records")[0]
    }


@router.get("/trades/summary")
async def get_trade_summary(
    start_date: date,
    end_date: date,
    athena: AthenaService = Depends(get_athena)
):
    """
    Get aggregated trade summary from archived data.

    Queries the trades table (archived trade data in S3).
    """
    df = athena.get_trade_summary(
        start_date.isoformat(),
        end_date.isoformat()
    )

    if df is None:
        raise HTTPException(status_code=500, detail="Query failed")

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": df.to_dict(orient="records")
    }


@router.get("/pnl/analysis")
async def get_pnl_analysis(
    commodity: CommodityType,
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    athena: AthenaService = Depends(get_athena)
):
    """
    Analyze daily P&L patterns using Athena window functions.

    Calculates:
    - Daily price changes
    - Percentage changes
    - Significant moves

    This demonstrates Athena's analytical SQL capabilities.
    """
    df = athena.get_daily_pnl_analysis(commodity.value, year, month)

    if df is None:
        raise HTTPException(status_code=500, detail="Query failed")

    # Calculate summary stats from results
    if len(df) > 0:
        pct_changes = df['pct_change'].astype(float)
        summary = {
            "avg_daily_change_pct": float(pct_changes.mean()),
            "max_gain_pct": float(pct_changes.max()),
            "max_loss_pct": float(pct_changes.min()),
            "volatility": float(pct_changes.std()),
            "positive_days": int((pct_changes > 0).sum()),
            "negative_days": int((pct_changes < 0).sum()),
        }
    else:
        summary = {}

    return {
        "commodity": commodity.value,
        "period": f"{year}-{month:02d}",
        "daily_data": df.to_dict(orient="records"),
        "summary": summary
    }


@router.post("/partitions/refresh")
async def refresh_partitions(
    table_name: str = Query(..., regex="^(prices|trades)$"),
    athena: AthenaService = Depends(get_athena)
):
    """
    Refresh table partitions to discover new S3 data.

    When new data is uploaded to S3, Athena needs to know
    about new partitions. Run this after adding data.
    """
    success = athena.refresh_partitions(table_name)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh partitions"
        )

    return {
        "message": f"Partitions refreshed for {table_name}",
        "table": table_name
    }


@router.get("/cost-estimate")
async def estimate_query_cost(
    query: str,
    athena: AthenaService = Depends(get_athena)
):
    """
    Estimate the cost of running a query.

    Athena pricing:
    - ~$5 per TB of data scanned
    - Minimum charge: 10 MB per query

    Tips to reduce costs:
    - Use partitioned tables
    - Use columnar formats (Parquet)
    - Limit columns in SELECT
    - Use LIMIT clause for testing
    """
    estimate = athena.get_query_cost_estimate(query)

    return {
        "query": query[:100] + "..." if len(query) > 100 else query,
        "estimate": estimate,
        "pricing_info": {
            "rate": "$5 per TB scanned",
            "minimum": "10 MB per query"
        }
    }


@router.get("/info")
async def get_athena_info(athena: AthenaService = Depends(get_athena)):
    """
    Get Athena configuration and connection info.
    """
    return {
        "database": athena.database,
        "data_bucket": athena.data_bucket,
        "results_bucket": athena.results_bucket,
        "region": athena.region,
        "tables": ["prices", "trades"],
        "documentation": {
            "athena_sql": "https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html",
            "pricing": "https://aws.amazon.com/athena/pricing/"
        }
    }
