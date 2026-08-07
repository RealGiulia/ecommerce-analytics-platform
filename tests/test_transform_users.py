from etl.transform.users import transform_users

RAW_USER = {
    "id": 1,
    "firstName": "Emily",
    "lastName": "Johnson",
    "age": 29,
    "gender": "female",
    "email": "emily.johnson@x.dummyjson.com",
    "phone": "+81 965-431-3024",
    "username": "emilys",
    "password": "emilyspass",
    "birthDate": "1996-5-30",
    "role": "admin",
    "university": "University of Wisconsin--Madison",
    "ssn": "900-590-289",
    "ein": "977-175",
    "ip": "42.48.100.32",
    "macAddress": "47:fa:41:18:ec:eb",
    "address": {
        "address": "626 Main Street",
        "city": "Phoenix",
        "state": "Mississippi",
        "stateCode": "MS",
        "postalCode": "29112",
        "country": "United States",
    },
    "company": {"department": "Engineering", "name": "Acme", "title": "Sales Manager"},
    "bank": {"cardNumber": "3693233511855044"},
    "crypto": {"wallet": "0xabc"},
}


def test_transform_users_flattens_nested_fields():
    df = transform_users([RAW_USER])

    assert len(df) == 1
    row = df.iloc[0]
    assert row["user_id"] == 1
    assert row["city"] == "Phoenix"
    assert row["company_name"] == "Acme"
    assert row["company_title"] == "Sales Manager"


def test_transform_users_drops_sensitive_fields():
    df = transform_users([RAW_USER])

    for column in ("password", "ssn", "ein", "ip", "mac_address", "bank", "crypto"):
        assert column not in df.columns


def test_transform_users_empty_input_returns_empty_dataframe():
    df = transform_users([])

    assert df.empty
