from sqlalchemy.engine.url import make_url

u = make_url("postgresql+asyncpg://user:pass@host/db")
print(f"Original: {u.drivername}")
u2 = u.set(drivername="postgresql+psycopg")
print(f"New: {u2.drivername}")
print(f"String: {u2.render_as_string(hide_password=True)}")
