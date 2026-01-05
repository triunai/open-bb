import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import socket
import ssl
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Supavisor Connection Details (IPv4 compatible)
# Using resolved IP from brute force: aws-1-ap-south-1.pooler.supabase.com
HOST = "aws-1-ap-south-1.pooler.supabase.com"
PORT = 5432
# Username format: [user].[project_ref]
USER = "postgres.pxnuylvyrcefeovlpolt" 
PASSWORD = "database-password%40" # properly encoded
DB = "postgres"

async def test():
    print(f"Using hardcoded IP: {HOST}...")
    
    # Use IP in URL
    database_url = f"postgresql+asyncpg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
    
    # Custom SSL context to allow IP connection (hostname mismatch check disabled)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE 
    
    e = create_async_engine(
        database_url,
        connect_args={"ssl": ssl_ctx}
    )
    
    print(f"Connecting to {HOST}:{PORT}...")
    try:
        async with e.connect() as c:
            r = await c.execute(text('SELECT version()'))
            v = r.scalar()
            print(f"Success! DB Version: {v}")
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await e.dispose()

if __name__ == "__main__":
    asyncio.run(test())
