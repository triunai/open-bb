import asyncio
import sys
from ofac_scanner.presentation.api.dependencies import get_event_query_service
from ofac_scanner.infrastructure.database import get_session_factory
from ofac_scanner.infrastructure.database.repositories import SQLEventRepository
from ofac_scanner.application.services import EventQueryService

# Windows loop fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_health_logic():
    print("Testing health check logic...")
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            print("Session created.")
            repo = SQLEventRepository(session)
            service = EventQueryService(repo)
            print("Service created. calling get_stats()...")
            stats = await service.get_stats()
            print(f"Stats: {stats}")
            print("Health check logic SUCCESS.")
    except Exception as e:
        print("Health check logic FAILED.")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_health_logic())
