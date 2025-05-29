import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def get_bedrock_fuid(gamertag):
    """Get a Bedrock player's FUID using the mcprofile.io API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://mcprofile.io/api/v1/bedrock/gamertag/{gamertag}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    fuid = data.get('floodgateuid')
                    if fuid and fuid != "00000000-0000-0000-0000-000000000000":
                        return fuid, gamertag
                return None, None
    except Exception as e:
        print(f"Error getting Bedrock FUID: {e}")
        return None, None

async def verify_floodgate_uuid(username):
    """Verify a Bedrock player's UUID using the Floodgate API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{FLOODGATE_API_ENDPOINT}/verify/{username}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('uuid')
                return None
    except Exception as e:
        print(f"Error verifying Floodgate UUID: {e}")
        return None 