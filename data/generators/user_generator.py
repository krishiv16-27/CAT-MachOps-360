"""Generate user accounts for all operators + staff roles."""
import hashlib
import uuid
from .faker_setup import uid


def _simple_hash(password: str) -> str:
    """
    Use bcrypt if available, else a SHA-256 placeholder.
    The backend re-hashes properly — this is for the seed SQL only.
    In practice the seed.py in the backend uses passlib directly.
    """
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return ctx.hash(password[:72])
    except Exception:
        # Fallback: sha256 placeholder (not secure, only for dataset file)
        return "sha256$" + hashlib.sha256(password.encode()).hexdigest()


# Default password for all demo users
DEFAULT_PASSWORD = "demo1234"


def generate_users(operators: list[dict], num_extra: int = 5) -> list[dict]:
    users = []

    # Staff accounts
    staff = [
        ("engineer@cat.com",    "Alex Engineer",    "engineer"),
        ("supervisor@cat.com",  "Sam Supervisor",   "supervisor"),
        ("safety@cat.com",      "Chris Safety",     "safety_officer"),
        ("admin@cat.com",       "Admin User",       "admin"),
        ("maintenance@cat.com", "Pat Maintenance",  "maintenance_engineer"),
    ]
    for email, name, role in staff[:num_extra]:
        users.append({
            "user_id": uid(),
            "email": email,
            "name": name,
            "hashed_password": _simple_hash(DEFAULT_PASSWORD),
            "role": role,
            "is_active": True,
            "operator_id": None,
        })

    # Operator accounts — one per operator
    for op in operators:
        code = op["employee_code"].lower()
        users.append({
            "user_id": uid(),
            "email": f"{code}@catsite.com",
            "name": op["name"],
            "hashed_password": _simple_hash(DEFAULT_PASSWORD),
            "role": "operator",
            "is_active": True,
            "operator_id": op["operator_id"],
        })

    return users


def generate_operator_certifications(operators: list[dict]) -> list[dict]:
    records = []
    for op in operators:
        if op.get("certification"):
            from datetime import date, timedelta
            expiry = date.fromisoformat(op["certification_expiry"]) if op.get("certification_expiry") else date.today() + timedelta(days=365)
            records.append({
                "cert_id": uid(),
                "operator_id": op["operator_id"],
                "cert_type": "Machine Operation",
                "cert_code": op["certification"],
                "issued_date": (expiry - timedelta(days=730)).isoformat(),
                "expiry_date": expiry.isoformat(),
                "issuing_body": "Caterpillar Training Institute",
                "is_valid": expiry >= date.today(),
            })
    return records
