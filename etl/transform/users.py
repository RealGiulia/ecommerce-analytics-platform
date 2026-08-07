"""Bronze -> silver transformation for the users entity.

DummyJSON's fake user records include sensitive-looking fields (password,
SSN, bank card number, crypto wallet, IP/MAC address, raw user agent).
None of that has analytical value, so it is deliberately excluded here
rather than carried downstream into the silver layer or warehouse -- the
same principle applied to real PII in a production pipeline.
"""

from __future__ import annotations

import pandas as pd

from etl.transform.cleaning import dedupe_by_id, utcnow


def transform_users(raw_users: list[dict]) -> pd.DataFrame:
    if not raw_users:
        return pd.DataFrame()

    ingested_at = utcnow()
    rows = []
    for user in raw_users:
        address = user.get("address") or {}
        company = user.get("company") or {}
        rows.append(
            {
                "user_id": user["id"],
                "first_name": user.get("firstName"),
                "last_name": user.get("lastName"),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "username": user.get("username"),
                "age": user.get("age"),
                "gender": user.get("gender"),
                "birth_date": user.get("birthDate"),
                "role": user.get("role"),
                "university": user.get("university"),
                "company_name": company.get("name"),
                "company_department": company.get("department"),
                "company_title": company.get("title"),
                "address": address.get("address"),
                "city": address.get("city"),
                "state": address.get("state"),
                "state_code": address.get("stateCode"),
                "postal_code": address.get("postalCode"),
                "country": address.get("country"),
                "ingested_at": ingested_at,
            }
        )

    df = pd.DataFrame(rows)
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce").dt.date
    df["age"] = df["age"].astype("Int64")

    return dedupe_by_id(df, "user_id")
