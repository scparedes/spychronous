from multiprocessing import Pool
import sys
import signal
import logging
from functools import wraps

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger(__name__)

class AsyncJob(object):
    def __init__(self, func=None, items=[], processes=4, timeout=60, max_retries=1, raise_child_exceptions=True):
        self.func = func
        self.items = items
        self.processes = processes
        self.timeout = timeout
        self.max_retries = max_retries
        self.raise_child_exceptions = raise_child_exceptions

    # Ctrl+C/SIGINT handling based no https://stackoverflow.com/a/35134329/3577492
    def run(self, items=[], debug=False):
        if not items:
            if not self.items and debug:
                LOG.info('No items...no work to be done.')
            items = self.items
        if debug:
            LOG.info('Beginning asynchronous job...')
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN) # Make the process ignore SIGINT before a process Pool is created. This way created child processes inherit SIGINT handler.
        pool = Pool(processes=self.processes)
        signal.signal(signal.SIGINT, original_sigint_handler) # Restore the original SIGINT handler in the parent process after a Pool has been created.
        worker_results = [] # list of AsyncResult's
        for item in items:
            worker_results.append(pool.apply_async(self.retry))
        pool.close() # no more work will be submitted to workers
        for r in worker_results:
            try:
                r.get(self.timeout) # check workers for errors -- wait on the results with timeout because the default blocking-waits ignore all signals.
            except KeyboardInterrupt:
                LOG.info('caught KeyboardInterrupt, terminating workers')
                pool.terminate()
                raise
            except Exception as e:
                if self.raise_child_exceptions:
                    pool.terminate()
                    raise e
                else:
                    if debug:
                        LOG.info("Reporting '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))

        pool.join() # wait for worker processes to terminate
        if debug:
            LOG.info('finished...')

    def retry(self):
        @wraps(self.handler)
        def wrapped(*args, **kwargs):
            retries = 0
            while retries < self.max_retries:
                try:
                    return self.handler(*args, **kwargs)
                except Exception:
                    pass
                retries += 1
        return wrapped

    def handler(self):
        def wrapper():
            try:
                self.func(self.items)
            except Exception as e:
                import traceback
                traceback.print_exc()
                LOG.error(traceback.format_exc())
                raise e
        return wrapper()

def useless_func(number):
    import time
    from random import random
    time.sleep(random()*5)
    if number == 2:
        1/0
    LOG.info(number)

if __name__=='__main__':
    numbers = [1,2,3,4,5]
    async_job = AsyncJob(func=useless_func, items=numbers, raise_child_exceptions=False)
    async_job.run(debug=True)