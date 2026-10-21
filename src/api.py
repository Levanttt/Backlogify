import concurrent.futures
from howlongtobeatpy import HowLongToBeat
HLTB_TIMEOUT_SECONDS = 15
HLTB_MAX_ATTEMPTS = 2


def get_estimated_hours(title):
    attempt = 0
    while attempt < HLTB_MAX_ATTEMPTS:
        attempt += 1
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(HowLongToBeat().search, title)
            results = future.result(timeout=HLTB_TIMEOUT_SECONDS)

            if not results:
                return None 

            best_match = max(results, key=lambda r: r.similarity)
            durations = {
                "main_story": float(best_match.main_story) if best_match.main_story else None,
                "main_extra": float(best_match.main_extra) if best_match.main_extra else None,
                "completionist": float(best_match.completionist) if best_match.completionist else None,
            }
            if all(jam is None for jam in durations.values()):
                return None
            return durations
        except concurrent.futures.TimeoutError:
            print(f"[HLTB ERROR] Timeout setelah {HLTB_TIMEOUT_SECONDS} detik (percobaan {attempt}/{HLTB_MAX_ATTEMPTS})")
        except Exception as e:
            print(f"[HLTB ERROR] {type(e).__name__}: {e} (percobaan {attempt}/{HLTB_MAX_ATTEMPTS})")
        finally:
            executor.shutdown(wait=False)
    return None
