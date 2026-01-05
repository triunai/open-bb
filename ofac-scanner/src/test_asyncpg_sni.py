import asyncio
import asyncpg
import ssl
import sys

# Fix loop on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HOST_IP = "13.200.110.68" # One of the IPs for aws-1-ap-south-1.pooler.supabase.com
HOSTNAME = "aws-1-ap-south-1.pooler.supabase.com"
USER = "postgres.pxnuylvyrcefeovlpolt"
PASS = "database-password@"
DB = "postgres"

async def test():
    print("Testing asyncpg with server_hostname...")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        conn = await asyncpg.connect(
            user=USER,
            password=PASS,
            database=DB,
            host=HOST_IP,
            port=5432,
            ssl=ctx,
            server_hostname=HOSTNAME
        )
        print("SUCCESS! Connected.")
        await conn.close()
    except TypeError as e:
        print(f"TypeError Failed: {e}")
    except Exception as e:
        print(f"Other Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
