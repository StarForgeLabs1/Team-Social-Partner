from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import csv
import io
from datetime import datetime
from backend.db import get_pg_pool
from backend.security import SecurityManager

router = APIRouter(prefix="/api/accounts", tags=["import-export"])

class SocialAccountImport(BaseModel):
    platform: str
    account_handle: str
    account_id: str = None
    access_token: str = None
    refresh_token: str = None

class AccountImportRequest(BaseModel):
    user_id: str
    accounts: List[SocialAccountImport]

class AccountExportResponse(BaseModel):
    user_id: str
    export_date: datetime
    accounts: List[Dict[str, Any]]

security_manager = SecurityManager()

@router.post("/import")
async def import_accounts(import_data: AccountImportRequest):
    """Import social accounts from JSON data"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(import_data.user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            imported_accounts = []
            failed_imports = []
            
            for account in import_data.accounts:
                try:
                    # Check if account already exists
                    existing = await connection.fetchrow(
                        """SELECT id FROM social_accounts 
                           WHERE platform = $1 AND account_handle = $2""",
                        account.platform, account.account_handle
                    )
                    
                    if existing:
                        failed_imports.append({
                            "account": account.account_handle,
                            "platform": account.platform,
                            "reason": "Account already exists"
                        })
                        continue
                    
                    # Encrypt sensitive data if provided
                    encrypted_access_token = None
                    encrypted_refresh_token = None
                    
                    if account.access_token:
                        encrypted_access_token = security_manager.encrypt(account.access_token)
                    if account.refresh_token:
                        encrypted_refresh_token = security_manager.encrypt(account.refresh_token)
                    
                    # Insert account
                    account_id = await connection.fetchval(
                        """INSERT INTO social_accounts 
                           (user_id, platform, account_handle, account_id, access_token, refresh_token)
                           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                        uuid.UUID(import_data.user_id), account.platform, 
                        account.account_handle, account.account_id,
                        encrypted_access_token, encrypted_refresh_token
                    )
                    
                    imported_accounts.append({
                        "id": str(account_id),
                        "platform": account.platform,
                        "account_handle": account.account_handle
                    })
                    
                except Exception as e:
                    failed_imports.append({
                        "account": account.account_handle,
                        "platform": account.platform,
                        "reason": str(e)
                    })
            
            return {
                "message": "Import completed",
                "imported_count": len(imported_accounts),
                "failed_count": len(failed_imports),
                "imported_accounts": imported_accounts,
                "failed_imports": failed_imports
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

@router.post("/import-csv")
async def import_accounts_csv(user_id: str, file: UploadFile = File(...)):
    """Import social accounts from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    pool = await get_pg_pool()
    
    try:
        # Read CSV content
        content = await file.read()
        csv_data = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            imported_accounts = []
            failed_imports = []
            
            for row in csv_reader:
                try:
                    # Expected CSV columns: platform, account_handle, account_id, access_token, refresh_token
                    platform = row.get('platform', '').strip()
                    account_handle = row.get('account_handle', '').strip()
                    
                    if not platform or not account_handle:
                        failed_imports.append({
                            "row": row,
                            "reason": "Missing required fields: platform and account_handle"
                        })
                        continue
                    
                    # Check if account already exists
                    existing = await connection.fetchrow(
                        """SELECT id FROM social_accounts 
                           WHERE platform = $1 AND account_handle = $2""",
                        platform, account_handle
                    )
                    
                    if existing:
                        failed_imports.append({
                            "account": account_handle,
                            "platform": platform,
                            "reason": "Account already exists"
                        })
                        continue
                    
                    # Encrypt tokens if provided
                    access_token = row.get('access_token', '').strip()
                    refresh_token = row.get('refresh_token', '').strip()
                    
                    encrypted_access_token = security_manager.encrypt(access_token) if access_token else None
                    encrypted_refresh_token = security_manager.encrypt(refresh_token) if refresh_token else None
                    
                    # Insert account
                    account_id = await connection.fetchval(
                        """INSERT INTO social_accounts 
                           (user_id, platform, account_handle, account_id, access_token, refresh_token)
                           VALUES ($1, $2, $3, $4, $5, $6) RETURNING id""",
                        uuid.UUID(user_id), platform, account_handle,
                        row.get('account_id', '').strip() or None,
                        encrypted_access_token, encrypted_refresh_token
                    )
                    
                    imported_accounts.append({
                        "id": str(account_id),
                        "platform": platform,
                        "account_handle": account_handle
                    })
                    
                except Exception as e:
                    failed_imports.append({
                        "row": row,
                        "reason": str(e)
                    })
            
            return {
                "message": "CSV import completed",
                "imported_count": len(imported_accounts),
                "failed_count": len(failed_imports),
                "imported_accounts": imported_accounts,
                "failed_imports": failed_imports
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV import error: {str(e)}")

@router.get("/export/{user_id}", response_model=AccountExportResponse)
async def export_accounts(user_id: str):
    """Export all social accounts for a user"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Fetch all accounts for the user (excluding sensitive tokens)
            accounts = await connection.fetch(
                """SELECT id, platform, account_handle, account_id, account_status, created_at, updated_at
                   FROM social_accounts WHERE user_id = $1 ORDER BY created_at DESC""",
                uuid.UUID(user_id)
            )
            
            export_data = []
            for account in accounts:
                export_data.append({
                    "id": str(account['id']),
                    "platform": account['platform'],
                    "account_handle": account['account_handle'],
                    "account_id": account['account_id'],
                    "account_status": account['account_status'],
                    "created_at": account['created_at'].isoformat(),
                    "updated_at": account['updated_at'].isoformat()
                })
            
            return AccountExportResponse(
                user_id=user_id,
                export_date=datetime.utcnow(),
                accounts=export_data
            )
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@router.get("/export-csv/{user_id}")
async def export_accounts_csv(user_id: str):
    """Export social accounts as CSV file"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id, user_account FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Fetch all accounts
            accounts = await connection.fetch(
                """SELECT platform, account_handle, account_id, account_status, created_at
                   FROM social_accounts WHERE user_id = $1 ORDER BY platform, account_handle""",
                uuid.UUID(user_id)
            )
            
            # Create CSV content
            output = io.StringIO()
            fieldnames = ['platform', 'account_handle', 'account_id', 'account_status', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            for account in accounts:
                writer.writerow({
                    'platform': account['platform'],
                    'account_handle': account['account_handle'],
                    'account_id': account['account_id'] or '',
                    'account_status': account['account_status'],
                    'created_at': account['created_at'].isoformat()
                })
            
            csv_content = output.getvalue()
            output.close()
            
            # Return CSV file
            filename = f"social_accounts_{user['user_account']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export error: {str(e)}")

@router.post("/bulk-update-status")
async def bulk_update_account_status(
    user_id: str, 
    account_ids: List[str], 
    new_status: str
):
    """Bulk update account status"""
    valid_statuses = ['active', 'inactive', 'suspended', 'pending']
    
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            updated_accounts = []
            failed_updates = []
            
            for account_id in account_ids:
                try:
                    # Check if account exists and belongs to user
                    account = await connection.fetchrow(
                        """SELECT id, account_handle, platform FROM social_accounts 
                           WHERE id = $1 AND user_id = $2""",
                        uuid.UUID(account_id), uuid.UUID(user_id)
                    )
                    
                    if not account:
                        failed_updates.append({
                            "account_id": account_id,
                            "reason": "Account not found or access denied"
                        })
                        continue
                    
                    # Update status
                    await connection.execute(
                        """UPDATE social_accounts 
                           SET account_status = $1, updated_at = $2 
                           WHERE id = $3""",
                        new_status, datetime.utcnow(), uuid.UUID(account_id)
                    )
                    
                    updated_accounts.append({
                        "account_id": account_id,
                        "account_handle": account['account_handle'],
                        "platform": account['platform'],
                        "new_status": new_status
                    })
                    
                except Exception as e:
                    failed_updates.append({
                        "account_id": account_id,
                        "reason": str(e)
                    })
            
            return {
                "message": "Bulk status update completed",
                "updated_count": len(updated_accounts),
                "failed_count": len(failed_updates),
                "updated_accounts": updated_accounts,
                "failed_updates": failed_updates
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk update error: {str(e)}")

@router.delete("/bulk-delete")
async def bulk_delete_accounts(user_id: str, account_ids: List[str]):
    """Bulk delete social accounts"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Verify user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            deleted_accounts = []
            failed_deletes = []
            
            for account_id in account_ids:
                try:
                    # Check if account exists and belongs to user
                    account = await connection.fetchrow(
                        """SELECT id, account_handle, platform FROM social_accounts 
                           WHERE id = $1 AND user_id = $2""",
                        uuid.UUID(account_id), uuid.UUID(user_id)
                    )
                    
                    if not account:
                        failed_deletes.append({
                            "account_id": account_id,
                            "reason": "Account not found or access denied"
                        })
                        continue
                    
                    # Delete account (CASCADE will handle related posts)
                    await connection.execute(
                        "DELETE FROM social_accounts WHERE id = $1",
                        uuid.UUID(account_id)
                    )
                    
                    deleted_accounts.append({
                        "account_id": account_id,
                        "account_handle": account['account_handle'],
                        "platform": account['platform']
                    })
                    
                except Exception as e:
                    failed_deletes.append({
                        "account_id": account_id,
                        "reason": str(e)
                    })
            
            return {
                "message": "Bulk delete completed",
                "deleted_count": len(deleted_accounts),
                "failed_count": len(failed_deletes),
                "deleted_accounts": deleted_accounts,
                "failed_deletes": failed_deletes
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk delete error: {str(e)}")