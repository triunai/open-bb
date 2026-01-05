import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import socket

# Windows loop fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

HOST = "aws-1-ap-south-1.pooler.supabase.com"
URL = "postgresql+psycopg://postgres.pxnuylvyrcefeovlpolt:database-password%40@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

async def test_psycopg():
    print("Resolving IP...")
    ip = socket.gethostbyname(HOST)
    print(f"IP: {ip}")
    
    print("Creating Engine...")
    engine = create_async_engine(
        URL, 
        echo=True, 
        connect_args={"hostaddr": ip, "sslmode": "require"}
    )
    
    print("Connecting...")
    async with engine.connect() as conn:
        print("Connected!")
        result = await conn.execute(text("SELECT version()"))
        print(result.scalar())
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_psycopg())
