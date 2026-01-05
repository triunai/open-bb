from ofac_scanner.config import get_settings
from sqlalchemy.engine import make_url
from urllib.parse import quote_plus
import sys

# Windows loop fix just in case
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    settings = get_settings()
    url_str = settings.database_url
    print(f"RAW URL: {url_str}")
    
    u = make_url(url_str)
    print(f"Parsed Driver: {u.drivername}")
    print(f"Parsed User:   {repr(u.username)}")
    print(f"Parsed Pass:   {repr(u.password)}")
    print(f"Parsed Host:   {repr(u.host)}")
    print(f"Parsed Port:   {u.port}")
    print(f"Parsed DB:     {u.database}")

    # Check for the specific issue
    if "@" in u.password if u.password else False:
        print("\n⚠️ WARNING: Password contains unescaped '@'")
    
    if u.host != "aws-1-ap-south-1.pooler.supabase.com":
        print(f"\n⚠️ WARNING: Host does not match expected 'aws-1-ap-south-1.pooler.supabase.com'")

except Exception as e:
    print(f"Error parsing: {e}")
