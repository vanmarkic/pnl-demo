"""
Contracts API Router - RESTful endpoints for contract management.

Learning points:
- FastAPI router organization
- Dependency injection for database sessions
- HTTP methods and status codes
- Pydantic validation in action
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from models.base import get_db
from models.contract import CommodityType
from schemas.contract import ContractCreate, ContractUpdate, ContractResponse, ContractList
from services.contract_service import ContractService

router = APIRouter(
    prefix="/api/contracts",
    tags=["contracts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=ContractResponse, status_code=201)
def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new energy contract.

    Example request body:
    ```json
    {
        "reference": "CTR-2025-001",
        "name": "Q1 2025 Gas Forward",
        "counterparty": "ENGIE Trading",
        "commodity": "GAS",
        "contract_type": "FORWARD",
        "volume": 10000,
        "unit_price": 35.50,
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-03-31T23:59:59"
    }
    ```
    """
    service = ContractService(db)

    # Check if reference already exists
    existing = service.get_by_reference(contract.reference)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Contract with reference {contract.reference} already exists"
        )

    return service.create(contract)


@router.get("/", response_model=ContractList)
def list_contracts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    commodity: Optional[CommodityType] = Query(None, description="Filter by commodity"),
    active_only: bool = Query(True, description="Only show active contracts"),
    db: Session = Depends(get_db)
):
    """
    List all contracts with pagination and filtering.

    Supports filtering by commodity type and active status.
    """
    service = ContractService(db)
    skip = (page - 1) * size

    contracts, total = service.get_all(
        skip=skip,
        limit=size,
        commodity=commodity,
        active_only=active_only
    )

    return ContractList(
        items=contracts,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/volume-summary")
def get_volume_summary(db: Session = Depends(get_db)):
    """
    Get total contracted volume by commodity.

    Useful for dashboard overview.
    """
    service = ContractService(db)
    return service.get_total_volume_by_commodity()


@router.get("/expiring")
def get_expiring_contracts(
    days: int = Query(30, ge=1, le=365, description="Days until expiration"),
    db: Session = Depends(get_db)
):
    """
    Get contracts expiring within N days.

    Important for contract lifecycle management.
    """
    service = ContractService(db)
    contracts = service.get_expiring_contracts(days)
    return {"expiring_contracts": contracts, "days": days}


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get a specific contract by ID."""
    service = ContractService(db)
    contract = service.get_by_id(contract_id)

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    update_data: ContractUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing contract.

    Only provided fields will be updated (partial update).
    """
    service = ContractService(db)
    contract = service.update(contract_id, update_data)

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """
    Delete (deactivate) a contract.

    Performs soft delete - sets is_active to 0.
    """
    service = ContractService(db)
    success = service.delete(contract_id)

    if not success:
        raise HTTPException(status_code=404, detail="Contract not found")

    return None
