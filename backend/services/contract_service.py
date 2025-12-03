"""
Contract Service - Business logic for contract operations.

Learning points:
- Service layer pattern (separates business logic from API)
- Dependency injection with SQLAlchemy sessions
- CRUD operations with proper error handling
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime

from models.contract import Contract, CommodityType, ContractType
from schemas.contract import ContractCreate, ContractUpdate


class ContractService:
    """
    Service class for contract operations.

    Follows Single Responsibility Principle - only handles contract logic.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, contract_data: ContractCreate) -> Contract:
        """Create a new contract"""
        contract = Contract(
            reference=contract_data.reference,
            name=contract_data.name,
            counterparty=contract_data.counterparty,
            commodity=contract_data.commodity,
            contract_type=contract_data.contract_type,
            volume=contract_data.volume,
            unit_price=contract_data.unit_price,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def get_by_id(self, contract_id: int) -> Optional[Contract]:
        """Get contract by ID"""
        return self.db.query(Contract).filter(Contract.id == contract_id).first()

    def get_by_reference(self, reference: str) -> Optional[Contract]:
        """Get contract by reference number"""
        return self.db.query(Contract).filter(Contract.reference == reference).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        commodity: Optional[CommodityType] = None,
        active_only: bool = True
    ) -> tuple[list[Contract], int]:
        """Get all contracts with optional filtering and pagination"""
        query = self.db.query(Contract)

        if active_only:
            query = query.filter(Contract.is_active == 1)

        if commodity:
            query = query.filter(Contract.commodity == commodity)

        total = query.count()
        contracts = query.offset(skip).limit(limit).all()

        return contracts, total

    def update(self, contract_id: int, update_data: ContractUpdate) -> Optional[Contract]:
        """Update an existing contract"""
        contract = self.get_by_id(contract_id)
        if not contract:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(contract, field, value)

        contract.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def delete(self, contract_id: int) -> bool:
        """Soft delete a contract (set is_active to 0)"""
        contract = self.get_by_id(contract_id)
        if not contract:
            return False

        contract.is_active = 0
        contract.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_total_volume_by_commodity(self) -> dict[str, float]:
        """Get total contracted volume grouped by commodity"""
        results = (
            self.db.query(
                Contract.commodity,
                func.sum(Contract.volume).label("total_volume")
            )
            .filter(Contract.is_active == 1)
            .group_by(Contract.commodity)
            .all()
        )
        return {r.commodity.value: r.total_volume for r in results}

    def get_expiring_contracts(self, days: int = 30) -> list[Contract]:
        """Get contracts expiring within N days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() + timedelta(days=days)

        return (
            self.db.query(Contract)
            .filter(Contract.is_active == 1)
            .filter(Contract.end_date <= cutoff_date)
            .order_by(Contract.end_date)
            .all()
        )
