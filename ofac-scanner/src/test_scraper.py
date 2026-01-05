"""Test the OFAC scraper."""
import asyncio
import sys

# Windows asyncio fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx

async def test_scrape():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://ofac.treasury.gov/recent-actions',
                timeout=30,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; OFACScanner/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            print(f"Status: {response.status_code}")
            print(f"Content length: {len(response.text)}")
            return response.text
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

if __name__ == "__main__":
    html = asyncio.run(test_scrape())
    if html:
        print("Success!")
