"""
Data API Router - S3 data operations and bulk data endpoints.

Learning points:
- File upload/download in FastAPI
- Streaming responses
- Async background tasks
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from datetime import date, datetime, timedelta
from typing import Optional
import pandas as pd
import io

from services.s3_service import get_s3_service, S3Service
from models.base import SessionLocal
from models.price import MarketPrice
from models.contract import CommodityType

router = APIRouter(
    prefix="/api/data",
    tags=["data"],
    responses={404: {"description": "Not found"}},
)


def get_s3() -> S3Service:
    """Dependency for S3 service."""
    return get_s3_service()


@router.post("/prices/upload")
async def upload_price_data(
    commodity: CommodityType,
    price_date: date,
    background_tasks: BackgroundTasks,
    s3: S3Service = Depends(get_s3)
):
    """
    Export price data from database to S3.

    This is an example of background task processing:
    - Returns immediately to client
    - Uploads data in background
    """
    def upload_task():
        db = SessionLocal()
        try:
            # Get prices from database
            prices = db.query(MarketPrice).filter(
                MarketPrice.commodity == commodity,
                MarketPrice.price_date == price_date
            ).all()

            if not prices:
                return

            # Convert to DataFrame
            df = pd.DataFrame([{
                'price_date': p.price_date.isoformat(),
                'commodity': p.commodity.value,
                'delivery_period': p.delivery_period,
                'price': p.price,
                'currency': p.currency,
                'price_type': p.price_type,
                'source': p.source
            } for p in prices])

            # Upload to S3
            s3.upload_price_data(commodity.value, price_date, df)
        finally:
            db.close()

    background_tasks.add_task(upload_task)

    return {
        "message": "Price data upload started",
        "commodity": commodity.value,
        "date": price_date.isoformat(),
        "status": "processing"
    }


@router.get("/prices/download")
async def download_price_data(
    commodity: CommodityType,
    price_date: date,
    s3: S3Service = Depends(get_s3)
):
    """
    Download price data from S3.

    Returns the data as a downloadable CSV file.
    """
    df = s3.get_price_data(commodity.value, price_date)

    if df is None:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for {commodity.value} on {price_date}"
        )

    # Convert to CSV for download
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    filename = f"prices_{commodity.value}_{price_date.isoformat()}.csv"

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/prices/list")
async def list_price_files(
    commodity: CommodityType,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    s3: S3Service = Depends(get_s3)
):
    """
    List available price data files in S3.
    """
    files = s3.list_price_files(commodity.value, year, month)

    return {
        "commodity": commodity.value,
        "filter": {"year": year, "month": month},
        "files": files,
        "count": len(files)
    }


@router.get("/prices/presigned-url")
async def get_presigned_url(
    commodity: CommodityType,
    price_date: date,
    expiration: int = Query(3600, ge=60, le=86400),
    s3: S3Service = Depends(get_s3)
):
    """
    Generate a presigned URL for direct S3 download.

    Useful for:
    - Large file downloads
    - Sharing with external systems
    - Bypassing API for data transfer
    """
    key = f"prices/{commodity.value}/{price_date.year}/{price_date.month:02d}/{price_date.isoformat()}.csv"
    url = s3.generate_presigned_url(key, expiration)

    if not url:
        raise HTTPException(
            status_code=404,
            detail="Could not generate presigned URL"
        )

    return {
        "url": url,
        "expires_in_seconds": expiration,
        "key": key
    }


@router.post("/archive/trades")
async def archive_trades(
    archive_date: date,
    background_tasks: BackgroundTasks,
    s3: S3Service = Depends(get_s3)
):
    """
    Archive trade data for a specific date to S3.
    """
    from models.trade import Trade

    def archive_task():
        db = SessionLocal()
        try:
            # Get trades for the date
            trades = db.query(Trade).filter(
                Trade.trade_date >= datetime.combine(archive_date, datetime.min.time()),
                Trade.trade_date < datetime.combine(archive_date + timedelta(days=1), datetime.min.time())
            ).all()

            if not trades:
                return

            # Convert to dict list
            trades_data = [{
                'trade_id': t.trade_id,
                'contract_id': t.contract_id,
                'direction': t.direction.value,
                'quantity': t.quantity,
                'price': t.price,
                'trade_date': t.trade_date.isoformat(),
                'delivery_date': t.delivery_date.isoformat(),
                'status': t.status.value,
                'trader': t.trader
            } for t in trades]

            # Archive to S3
            s3.archive_trades(trades_data, archive_date)
        finally:
            db.close()

    background_tasks.add_task(archive_task)

    return {
        "message": "Trade archive started",
        "date": archive_date.isoformat(),
        "status": "processing"
    }


@router.get("/archive/trades")
async def get_archived_trades(
    archive_date: date,
    s3: S3Service = Depends(get_s3)
):
    """
    Retrieve archived trade data from S3.
    """
    trades = s3.get_archived_trades(archive_date)

    if trades is None:
        raise HTTPException(
            status_code=404,
            detail=f"No archived trades found for {archive_date}"
        )

    return {
        "date": archive_date.isoformat(),
        "trades": trades,
        "count": len(trades)
    }


@router.get("/bucket/info")
async def get_bucket_info(s3: S3Service = Depends(get_s3)):
    """
    Get information about the S3 bucket.

    Useful for debugging and monitoring.
    """
    try:
        # Check if bucket exists
        exists = s3._check_bucket_exists()

        return {
            "bucket_name": s3.bucket_name,
            "region": s3.region,
            "exists": exists,
            "status": "connected" if exists else "not_found"
        }
    except Exception as e:
        return {
            "bucket_name": s3.bucket_name,
            "region": s3.region,
            "exists": False,
            "status": "error",
            "error": str(e)
        }
