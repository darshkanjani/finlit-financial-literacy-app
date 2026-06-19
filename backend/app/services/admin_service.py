"""

Admin data operations.

TODO (Leon):
- Make sure we never delete the last admin (optional safety rule)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import User, FinancialProfile, StressTestResult, AdviceHistory
from app.db.base import Base


def list_users(db: Session) -> list[dict]:
    rows = db.query(User).order_by(User.created_at.desc()).limit(200).all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "password hash": u.password_hash,
            "literacy score": u.literacy_score,
            "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else "",
            "has_profile": bool(getattr(u, "profile", None)),
            "is_admin": bool(u.is_admin),
        }
        for u in rows
    ]


def delete_user(db: Session, *, user_id: str) -> None:
    u = db.query(User).filter(User.id == user_id).first()
    
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    adminNum = get_stats(db)['admins'] #Check how many admins there are in the database
    if bool(u.is_admin) and adminNum == 1: #If the current user is an admin, and there is only one admin, prevent it from being deleted
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete the last admin")

    db.delete(u)
    db.commit()


def get_stats(db: Session) -> dict:
    total_users = db.query(User).count()
    profiles_completed = db.query(FinancialProfile).count()
    stress_tests_run = db.query(StressTestResult).count()
    advice_generated = db.query(AdviceHistory).count()

    return {
        "total_users": int(total_users),
        "profiles_completed": int(profiles_completed),
        "stress_tests_run": int(stress_tests_run),
        "advice_generated": int(advice_generated),
    }

def describe_Schema() -> None: 
    '''
    This function will: 
    1. Print number of tables in database
    2. Print the name of each table, followed by its structure
    To Use:
    Open python command line when located in the backend directory
    Import: from app.services.admin_service import describe_Schema
    Run: describe_Schema()
    '''
    tablesInfo = Base.metadata.tables
    num_Tables = len(tablesInfo)

    print(f"There are {num_Tables} tables in the database.\n")

    for table_name, table in tablesInfo.items():
        print(table_name.upper())

        for column in table.columns:
            print(f"  {column.type} {column.name}")
        
        print()

    

