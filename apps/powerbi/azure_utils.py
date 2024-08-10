# apps/powerbi/azure_utils.py

import os

import requests


def get_access_token():
    url = f"{os.getenv('PBI_AUTHORITYURL')}{os.getenv('PBI_TENANT')}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("PBI_APPLICATIONID"),
        "client_secret": os.getenv("PBI_APPLICATIONSECRET"),
        "scope": os.getenv("PBI_SCOPE"),
        "tenant": os.getenv("PBI_TENANT"),
    }
    response = requests.post(url, headers=headers, data=body)
    response.raise_for_status()
    return response.json().get("access_token")


def get_power_bi_headers():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    return headers
