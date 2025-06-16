"""
Tools for the ODIN Discord bot agent.
"""
import os
from loguru import logger
import httpx
import uuid as uuid_lib
from typing import Optional

# ========= API Constants =========
API_BASE_URL: str = "https://0din.ai/api/v1/threatfeed/"
API_KEY_NOT_CONFIGURED_MSG: str = "API key not configured."
API_REQUEST_FAILED_MSG: str = "API request failed: {error}"
API_RETURNED_STATUS_MSG: str = "API returned status code {status_code}: {text}"
INVALID_UUID_MSG: str = "The UUID you provided is not valid. Please provide a valid UUID."
SCANNED_MSG: str = "It has been scanned"
NOT_SCANNED_MSG: str = "It hasn't been checked, hang tight."

def is_valid_uuid(uuid_str: str, version: int = 4) -> bool:
    """Check if uuid_str is a valid UUID of the given version."""
    try:
        val = uuid_lib.UUID(uuid_str, version=version)
        return str(val) == uuid_str
    except (ValueError, AttributeError, TypeError):
        return False

def parse_scan_result(data: dict) -> str:
    """Extracts and formats the scan result from the API response."""
    for item in data.get("metadata", []):
        if item.get("type") == "ScannerModule":
            scanned = item.get("result")
            if scanned == 1:
                return SCANNED_MSG
            elif scanned == 0 or scanned is None:
                return NOT_SCANNED_MSG
    # If no ScannerModule or unexpected result, show full JSON
    import json
    return f"```json\n{json.dumps(data, indent=2)}\n```"

async def check_submission(uuid: str) -> str:
    """Check a UUID in the ODIN threat feed.
    
    Args:
        uuid: The UUID to check
        
    Returns:
        str: The scan result message
    """
    if not is_valid_uuid(uuid):
        return INVALID_UUID_MSG
    
    api_key = os.getenv("ODIN_API_KEY")
    if not api_key:
        logger.error("ODIN_API_KEY not set in environment.")
        return API_KEY_NOT_CONFIGURED_MSG
    
    api_url = f"{API_BASE_URL}{uuid}"
    headers = {
        "accept": "application/json",
        "Authorization": api_key
    }
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(api_url, headers=headers)
        logger.info(f'API request to {api_url} returned status {response.status_code}')
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return API_REQUEST_FAILED_MSG.format(error=e)
    
    if response.status_code != 200:
        logger.error(f"API returned status code {response.status_code}: {response.text}")
        return f"{API_RETURNED_STATUS_MSG.format(status_code=response.status_code, text=response.text)}\nDid you provide a valid UUID?"
    
    try:
        data = response.json()
    except Exception as e:
        logger.error(f'Error parsing JSON response: {e}')
        return response.text

    return parse_scan_result(data) 