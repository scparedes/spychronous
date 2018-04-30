from multiprocessing import Pool, Manager
import sys
import signal
import logging

LOG = logging.getLogger(__name__)

_hours = 60*60
DEFAULT_TIMEOUT = 15 * _hours

class Job(object):
    def __init__(self, func=None, items=[], args=[], processes=4, timeout=DEFAULT_TIMEOUT, retry=0, raise_child_exceptions=True):
        self.func = func
        self.items = items
        self.args = args
        self.processes = processes
        self.timeout = timeout
        self.retry = retry
        self.raise_child_exceptions = raise_child_exceptions
    
    def run_single_processed(self, debug=False): # this short circuits because work isn't requeued...
        if debug:
            LOG.info('Beginning single-processed job...')
        worker_outputs = list() # captures the return values of functions
        try:
            map(lambda x: run_function(self.func, worker_outputs, [x] + self.args), self.items)
        except Exception as e:
            if self.raise_child_exceptions:
                raise e
            else:
                if debug:
                    LOG.info("Logging '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))
        if debug:
            LOG.info('Finished job...')
        return worker_outputs

    # Ctrl+C/SIGINT handling based no https://stackoverflow.com/a/35134329/3577492
    def run_multi_processed(self, debug=False):
        if debug:
            LOG.info('Beginning multi-processed job...')
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN) # Make the process ignore SIGINT before a process Pool is created. This way created child processes inherit SIGINT run_function.
        manager = Manager()
        worker_outputs = manager.list() # captures the return values of functions
        pool = Pool(processes=self.processes)
        signal.signal(signal.SIGINT, original_sigint_handler) # Restore the original SIGINT run_function in the parent process after a Pool has been created.
        worker_statuses = [] # list of AsyncResult's
        for item in self.items:
            worker_statuses.append(pool.apply_async(run_function, [self.func, worker_outputs, [item] + self.args]))
        pool.close() # no more work will be submitted to workers
        for ws in worker_statuses:
            try:
                ws.get(self.timeout) # check workers for errors -- wait on the results with timeout because the default blocking-waits ignore all signals.
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
        return list(worker_outputs)

def run_function(some_function, worker_outputs, args):
    """
    This is a method that will be called by every job worker.
    They run the function and append the output of each run to
    worker outputs.
    """
    try:
        output = some_function(*args)
        worker_outputs.append(output)
    except Exception as e:
        import traceback
        LOG.error(traceback.format_exc())
        raise e

def useless_func(number):
    import time
    from random import random
    time.sleep(random()*5)
    if number == 2:
        1/0 # fails here
    LOG.info(number)

def another_useless_func(number, char):
    import time
    from random import random
    time.sleep(random()*5)
    if number == 2:
        LOG.info(char)

def outputting_useless_func(number):
    import time
    from random import random
    time.sleep(random()*5)
    return number

if __name__=='__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    numbers = [1,2,3,4,5]
    job = Job(func=useless_func, items=numbers, raise_child_exceptions=False)
    job.run_single_processed(debug=True)
    print 'Successfully ran single processed test!'
    job.run_multi_processed(debug=True)
    print 'Successfully ran multi processed test!'

    job = Job(func=another_useless_func, items=numbers, args=['b'])
    job.run_single_processed(debug=True)
    print 'Successfully ran single processed test!'
    job.run_multi_processed(debug=True)
    print 'Successfully ran multi processed test!'

    job = Job(func=outputting_useless_func, items=numbers)
    output = job.run_single_processed(debug=True)
    assert set(output) == set(numbers)
    print 'Successfully captured output of single processed test!'
    output = job.run_multi_processed(debug=True)
    assert set(output) == set(numbers)
    print 'Successfully captured output of multi processed test!'

