from multiprocessing import Pool
import sys
import signal
import logging

LOG = logging.getLogger(__name__)

_hours = 60*60
DEFAULT_TIMEOUT = 15 * _hours

class Job(object):
    def __init__(self, func=None, items=[], processes=4, timeout=DEFAULT_TIMEOUT, retry=0, raise_child_exceptions=True):
        self.func = func
        self.items = items
        self.processes = processes
        self.timeout = timeout
        self.retry = retry
        self.raise_child_exceptions = raise_child_exceptions
    
    def run_single_processed(self, debug=False):
        # if not self.items:
        #     if debug:
        #         LOG.info('No items...no work to be done.')
        #     return
        if debug:
            LOG.info('Beginning single-processed job...')
        try:
            map(lambda x: handler(self.func, x), self.items)
        except Exception as e:
            if self.raise_child_exceptions:
                raise e
            else:
                if debug:
                    LOG.info("Logging '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))
        if debug:
            LOG.info('Finished job...')

    # Ctrl+C/SIGINT handling based no https://stackoverflow.com/a/35134329/3577492
    def run_multi_processed(self, debug=False):
        # if not self.items:
        #     if debug:
        #         LOG.info('No items...no work to be done.')
        #     return
        if debug:
            LOG.info('Beginning multi-processed job...')
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN) # Make the process ignore SIGINT before a process Pool is created. This way created child processes inherit SIGINT handler.
        pool = Pool(processes=self.processes)
        signal.signal(signal.SIGINT, original_sigint_handler) # Restore the original SIGINT handler in the parent process after a Pool has been created.
        worker_results = [] # list of AsyncResult's
        for item in self.items:
            worker_results.append(pool.apply_async(handler, [self.func, item]))
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
                        LOG.info("Logging '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))

        pool.join() # wait for worker processes to terminate
        if debug:
            LOG.info('Finished job...')

def handler(some_function, *args):
    def wrapper():
        try:
            some_function(*args)
        except Exception as e:
            import traceback
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
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    numbers = [1,2,3,4,5]
    job = Job(func=useless_func, items=numbers, raise_child_exceptions=False)
    job.run_single_processed(debug=True)
    print 'Successfully ran single processed test!'
    job.run_multi_processed(debug=True)
    print 'Successfully ran multi processed test!'