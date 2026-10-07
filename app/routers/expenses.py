"""Expenses router: manage cycle expenditures with cycle-to-farm ownership validation."""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.dependencies import get_current_farmer
from app.routers.cycles import verify_cycle_ownership
from app.schemas import ExpenseCreateRequest, ExpenseResponse, MessageResponse

logger = logging.getLogger("agripredict.expenses")
router = APIRouter(tags=["Expenses"])


@router.post(
    "/cycles/{cycle_id}/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an expense for a crop cycle",
)
def create_expense(
    cycle_id: int,
    payload: ExpenseCreateRequest,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Add an expense item to a crop cycle.

    Ownership is checked through cycle -> farm -> farmer_id.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    insert_query = """
        INSERT INTO expenses (
            cycle_id, category, amount, expense_date, notes
        ) VALUES (
            %s, %s, %s, %s, %s
        )
    """
    expense_id = db.execute_insert(
        insert_query,
        (
            cycle_id,
            payload.category,
            payload.amount,
            payload.expense_date,
            payload.notes,
        ),
    )

    fetch_query = """
        SELECT expense_id, cycle_id, category, amount, expense_date, notes
        FROM expenses
        WHERE expense_id = %s
    """
    created = db.fetch_one(fetch_query, (expense_id,))

    return ExpenseResponse(
        expense_id=created["expense_id"],
        cycle_id=created["cycle_id"],
        category=created["category"],
        amount=float(created["amount"]),
        expense_date=created["expense_date"],
        notes=created.get("notes"),
    )


@router.get(
    "/cycles/{cycle_id}/expenses",
    response_model=List[ExpenseResponse],
    summary="List all expenses for a crop cycle",
)
def get_cycle_expenses(
    cycle_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Retrieve all expenses associated with a cycle.

    Ownership is validated to ensure the authenticated farmer owns the cycle.
    """
    farmer_id = current_farmer["farmer_id"]
    verify_cycle_ownership(cycle_id, farmer_id)

    query = """
        SELECT expense_id, cycle_id, category, amount, expense_date, notes
        FROM expenses
        WHERE cycle_id = %s
        ORDER BY expense_date DESC, expense_id DESC
    """
    rows = db.fetch_all(query, (cycle_id,))

    return [
        ExpenseResponse(
            expense_id=r["expense_id"],
            cycle_id=r["cycle_id"],
            category=r["category"],
            amount=float(r["amount"]),
            expense_date=r["expense_date"],
            notes=r.get("notes"),
        )
        for r in rows
    ]


@router.delete(
    "/expenses/{expense_id}",
    response_model=MessageResponse,
    summary="Delete an expense record",
)
def delete_expense(
    expense_id: int,
    current_farmer: Dict[str, Any] = Depends(get_current_farmer),
):
    """Delete an expense record.

    Ownership checked through expense -> cycle -> farm -> farmer_id.
    """
    farmer_id = current_farmer["farmer_id"]

    query = """
        SELECT
            e.expense_id,
            e.cycle_id,
            c.farm_id,
            f.farmer_id
        FROM expenses e
        JOIN crop_cycles c ON e.cycle_id = c.cycle_id
        JOIN farms f ON c.farm_id = f.farm_id
        WHERE e.expense_id = %s
    """
    row = db.fetch_one(query, (expense_id,))

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with ID {expense_id} not found",
        )

    if row["farmer_id"] != farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this expense",
        )

    db.execute_update("DELETE FROM expenses WHERE expense_id = %s", (expense_id,))

    return MessageResponse(
        detail=f"Expense #{expense_id} deleted successfully",
        success=True,
    )
