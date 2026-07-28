import multiprocessing
import random
import threading
import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CupsCallError(Exception):
    """A CUPS operation failed before producing a usable result."""


class CupsTimeoutError(CupsCallError):
    """A CUPS operation exceeded its deadline."""


def _cups_operation(connection_config, operation, arguments, result_pipe):
    """Run in a disposable process so a stuck libcups call can be killed."""
    try:
        import cups

        server, port = connection_config
        cups.setServer(server)
        cups.setPort(port)
        connection = cups.Connection(server, port)

        if operation == "get_printers":
            result = connection.getPrinters()
        elif operation == "print_file":
            result = connection.printFile(*arguments)
        else:
            raise ValueError("Unknown CUPS operation: %s" % operation)

        result_pipe.send(("ok", result))
    except BaseException as exc:
        result_pipe.send(("error", "%s: %s" % (type(exc).__name__, exc)))
    finally:
        result_pipe.close()


class IsolatedCupsClient:
    def __init__(
        self,
        server,
        port=631,
        list_timeout=5,
        print_timeout=20,
        worker_target=_cups_operation,
    ):
        self.server = server
        self.port = port
        self.list_timeout = list_timeout
        self.print_timeout = print_timeout
        self._worker_target = worker_target
        self._multiprocessing = multiprocessing.get_context("spawn")

    def _run(self, operation, arguments, timeout):
        receive_pipe, send_pipe = self._multiprocessing.Pipe(duplex=False)
        process = self._multiprocessing.Process(
            target=self._worker_target,
            args=((self.server, self.port), operation, arguments, send_pipe),
            daemon=True,
        )
        process.start()
        send_pipe.close()

        try:
            if not receive_pipe.poll(timeout):
                process.terminate()
                process.join(1)
                if process.is_alive():
                    process.kill()
                    process.join(1)
                raise CupsTimeoutError(
                    "CUPS %s timed out after %s seconds" % (operation, timeout)
                )

            status, value = receive_pipe.recv()
            process.join(1)
            if status == "error":
                raise CupsCallError(value)
            return value
        except EOFError:
            raise CupsCallError(
                "CUPS %s worker exited without a response" % operation
            )
        finally:
            receive_pipe.close()
            if process.is_alive():
                process.terminate()
                process.join(1)

    def get_printers(self):
        return self._run("get_printers", (), self.list_timeout)

    def print_file(self, printer_name, path, filename, options):
        return self._run(
            "print_file",
            (printer_name, path, filename, options),
            self.print_timeout,
        )


class PrinterCache:
    def __init__(
        self,
        cups_client,
        allowed_printers,
        refresh_interval=10,
        max_backoff=60,
        stale_after=None,
    ):
        self.cups_client = cups_client
        self.allowed_printers = set(allowed_printers)
        self.refresh_interval = refresh_interval
        self.max_backoff = max(max_backoff, refresh_interval)
        self.stale_after = stale_after or refresh_interval * 2

        self._lock = threading.Lock()
        self._start_lock = threading.Lock()
        self._started = False
        self._printers = []
        self._last_success = None
        self._last_attempt = None
        self._last_error = None

    def start(self):
        if self._started:
            return
        with self._start_lock:
            if self._started:
                return
            self._started = True
            thread = threading.Thread(
                target=self._refresh_loop,
                name="printer-cache-refresh",
                daemon=True,
            )
            thread.start()

    def refresh(self):
        attempted_at = datetime.now(timezone.utc)
        try:
            cups_printers = self.cups_client.get_printers()
            printers = [
                {**properties, "name": name}
                for name, properties in cups_printers.items()
                if name in self.allowed_printers
            ]
            with self._lock:
                self._printers = printers
                self._last_success = datetime.now(timezone.utc)
                self._last_attempt = attempted_at
                self._last_error = None
            return True
        except Exception as exc:
            logger.warning("Could not refresh printers from CUPS: %s", exc)
            with self._lock:
                self._last_attempt = attempted_at
                self._last_error = str(exc)
            return False

    def snapshot(self):
        now = datetime.now(timezone.utc)
        with self._lock:
            last_success = self._last_success
            stale = (
                last_success is None
                or self._last_error is not None
                or (now - last_success).total_seconds() > self.stale_after
            )
            return {
                "printers": list(self._printers),
                "stale": stale,
                "last_updated": (
                    last_success.isoformat() if last_success is not None else None
                ),
            }

    def _refresh_loop(self):
        failures = 0
        while True:
            if self.refresh():
                failures = 0
                delay = self.refresh_interval
            else:
                failures += 1
                delay = min(
                    self.refresh_interval * (2 ** (failures - 1)),
                    self.max_backoff,
                )

            jitter = random.uniform(0, min(1, delay * 0.1))
            time.sleep(delay + jitter)
