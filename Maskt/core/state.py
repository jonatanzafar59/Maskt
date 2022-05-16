from .pxLogManager import pxLogging
import os


class PxState(pxLogging):
    def __init__(self):
        super().__init__()
        self._state = None
        self._failures = 0

    def _state_success(self):
        self._state = "SUCCESS"
        # self._log_state()

    def _state_failed(self):
        self._state = "FAILED"
        if self.return_dict is not False:
            pid = os.getpid()
            self.return_dict[pid] = 1

    def _state_running(self):
        self._state = "RUNNING"
        # self._log_state()

    def _log_state(self):
        self.logger.debug(f'{self._state}')

    def _is_success(self):
        return self._state == "SUCCESS"

    def _is_failed(self):
        return self._state == "FAILED"

    def _is_running(self):
        return self._state == "RUNNING"

    def _is_retrying(self):
        return self._failures > 0
