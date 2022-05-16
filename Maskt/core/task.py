from interruptingcow import timeout
from .state import PxState, pxLogging
import time
import os
import queue
from multiprocessing import Process, Manager
import sys


class pxSpawn(pxLogging):
    def __init__(self):
        super().__init__()
        self.dry_run = None
        self._set_env()
        self.queue = queue.Queue()
        self.jobs = []
        manager = Manager()
        self.return_dict = manager.dict()

    def _consume_queue(self):
        while True:
            try:
                task = self.queue.get(False)
                p = Process(target=task.dispatch, args=(self.return_dict, ))
                self.jobs.append(p)
                p.start()

            except queue.Empty:
                break

        self._clean()

    def _clean(self):
        for j in self.jobs:
            j.join()
        self._set_exit_code()

    def _set_exit_code(self):
        return_codes = self.return_dict.values()
        code = 0 if return_codes == [] else 1
        sys.exit(code)

    def run_async(self, task):
        self.queue.put(task)

    def _set_env(self):
        os.environ['PXTASK'] = "1"
        self.dry_run = (
            os.getenv(
                'MASKT_DRYRUN',
                'False').lower() == 'true')  # NOT USED YET


class PxTask(PxState):
    def __init__(self, auto_run=True):
        super().__init__()
        if auto_run:
            self.dispatch()

    def pre_run(self):
        # This method gets called before `run` executed without raising any
        # exceptions.
        pass

    def post_run(self):
        # This method gets called when `run` completes without raising any
        # exceptions.
        pass

    def _run_wrapper(self):
        try:
            with timeout(self.timeout, exception=PxTaskTimeoutError):
                self.pre_run()
                self.run()
                self.post_run()
                self._state_success()
        except PxTaskTimeoutError:
            self.logger.error(f"Timeout")
            self._retry()
        except PxTaskExitGracefully as e:
            self.logger.info(e)
            self._state_success()
        except Exception as e:
            self.logger.error(e)
            self._retry()

    def _retry(self):
        self._failures += 1
        if self.retry_count >= self._failures:
            self.logger.error(
                f"Task failed {self._failures} time, retrying after {self.retry_delay} seconds delay")
            time.sleep(self.retry_delay)
            self._run_wrapper()
        else:
            self._state_failed()

    def dispatch(self, return_dict=False):
        self.return_dict = return_dict
        self._state_running()
        self._run_wrapper()

    @property
    def run_async(self):
        pass

    @property
    def name(self):
        return ""

    @property
    def timeout(self):
        return 999999

    @property
    def retry_count(self):
        return 0

    @property
    def retry_delay(self):
        return 0


class pxTaskManager(pxSpawn):
    def __init__(self):
        super().__init__()

    def start(self):
        self.run()
        self._consume_queue()

    def on_failure(self):
        # This method gets called after `run` in case of a failed run
        # Default value pass
        pass

    def on_success(self):
        # This method gets called after `run` in case of a successful run
        # Default value pass
        pass


class PxTaskTimeoutError(Exception):
    pass


class PxTaskFailure(Exception):
    pass


class PxTaskValidationFailure(Exception):
    pass

class PxTaskExitGracefully(Exception):
    pass

