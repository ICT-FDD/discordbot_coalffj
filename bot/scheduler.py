# bot/scheduler.py
import asyncio
from datetime import datetime, timedelta
import logging
import zoneinfo

log = logging.getLogger(__name__)

async def run_daily_07h_europe_brussels(job_coro):
    """
    Lance `job_coro` chaque jour à 07:00 Europe/Brussels.
    `job_coro` doit être une coroutine SANS argument.
    """
    tz = zoneinfo.ZoneInfo("Europe/Brussels")
    await asyncio.sleep(0)  # yield au loop

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)

        sleep_s = (target - now).total_seconds()
        log.info("[CORE] Prochaine exécution à %s (dans %d s)", target.isoformat(), int(sleep_s))

        try:
            await asyncio.sleep(sleep_s)
            await job_coro()
        except asyncio.CancelledError:
            log.info("[CORE] Tâche quotidienne annulée — arrêt propre.")
            raise
        except Exception:
            log.exception("[CORE] Erreur dans la tâche quotidienne — on continue.")
