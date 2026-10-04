from celery import shared_task
from .services import process_search
import asyncio


@shared_task
def run_search(search_id):
    asyncio.run(
        process_search(search_id)
    )