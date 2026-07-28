import time
import unittest

from printer_service import (
    CupsCallError,
    CupsTimeoutError,
    IsolatedCupsClient,
    PrinterCache,
)


def hanging_worker(connection_config, operation, arguments, result_pipe):
    time.sleep(10)


def failing_worker(connection_config, operation, arguments, result_pipe):
    result_pipe.send(("error", "simulated failure"))
    result_pipe.close()


class SequenceClient:
    def __init__(self, results):
        self.results = iter(results)

    def get_printers(self):
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return result


class PrinterCacheTests(unittest.TestCase):
    def test_successful_refresh_filters_and_publishes_printers(self):
        client = SequenceClient(
            [
                {
                    "allowed": {"printer-info": "Allowed"},
                    "hidden": {"printer-info": "Hidden"},
                }
            ]
        )
        cache = PrinterCache(client, ["allowed"])

        self.assertTrue(cache.refresh())
        snapshot = cache.snapshot()

        self.assertFalse(snapshot["stale"])
        self.assertEqual(
            snapshot["printers"],
            [{"printer-info": "Allowed", "name": "allowed"}],
        )
        self.assertIsNotNone(snapshot["last_updated"])

    def test_failed_refresh_preserves_last_successful_snapshot(self):
        client = SequenceClient(
            [
                {"allowed": {"printer-info": "Last known"}},
                CupsCallError("offline"),
            ]
        )
        cache = PrinterCache(client, ["allowed"])

        self.assertTrue(cache.refresh())
        last_updated = cache.snapshot()["last_updated"]
        self.assertFalse(cache.refresh())
        snapshot = cache.snapshot()

        self.assertTrue(snapshot["stale"])
        self.assertEqual(snapshot["last_updated"], last_updated)
        self.assertEqual(snapshot["printers"][0]["printer-info"], "Last known")

    def test_cache_recovers_after_an_intermediate_failure(self):
        client = SequenceClient(
            [
                CupsCallError("offline"),
                {"allowed": {"printer-info": "Recovered"}},
            ]
        )
        cache = PrinterCache(client, ["allowed"])

        self.assertFalse(cache.refresh())
        self.assertTrue(cache.snapshot()["stale"])
        self.assertTrue(cache.refresh())

        snapshot = cache.snapshot()
        self.assertFalse(snapshot["stale"])
        self.assertEqual(snapshot["printers"][0]["printer-info"], "Recovered")


class IsolatedCupsClientTests(unittest.TestCase):
    def test_hung_native_operation_is_terminated_at_deadline(self):
        client = IsolatedCupsClient(
            "unused",
            list_timeout=0.2,
            worker_target=hanging_worker,
        )

        started = time.monotonic()
        with self.assertRaises(CupsTimeoutError):
            client.get_printers()

        self.assertLess(time.monotonic() - started, 2)

    def test_worker_errors_are_returned_as_controlled_exceptions(self):
        client = IsolatedCupsClient(
            "unused",
            worker_target=failing_worker,
        )

        with self.assertRaisesRegex(CupsCallError, "simulated failure"):
            client.get_printers()


if __name__ == "__main__":
    unittest.main()
