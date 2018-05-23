from multiprocessing import Pool, Manager
from non_daemonic_process.non_daemonic_processing import NoDaemonProcessPool
import sys
import signal

import traceback
import logging

LOG = logging.getLogger(__name__)

HOURS = 60*60
DAYS = HOURS*24
DEFAULT_TIMEOUT = 30 * DAYS

class SynchronousJob(object):
    """A synchronous Job-runner that leverages parallel processing to apply a function to each item in a list.
        Args:
            func (function): The function that's applied to each item -- the first parameter must represent a single item from items.
            items (list): The dataset that's iterated over and transformed with func.
            args (list): The additional parameters in func's signature proceeding the first required parameter.
            processes (int):The number of processes you want to enlist for parallelization.
            timeout (int): The number of seconds a given process in the process pool has to complete its work.
            no_daemon (bool): This allows processes in the process pool to spawn more pools of processes.
            suppress_worker_exceptions (bool): Prevents killing a SynchronousJob and its workers when any given coworker raises an exception.
    """
    def __init__(self, func=None, items=[], args=[], processes=4, timeout=DEFAULT_TIMEOUT, no_daemon=False, suppress_worker_exceptions=False):
        self.func = func
        self.items = items
        self.args = args
        self.processes = processes
        self.timeout = timeout
        self.no_daemon = no_daemon
        self.suppress_worker_exceptions = suppress_worker_exceptions
    
    def run_single_processed(self, log_start_finish=False):
        if log_start_finish:
            LOG.info('Beginning single-processed SynchronousJob...')
        worker_outputs = list() # This will accumulate return values of 'func'.
        for item in self.items:
            try:
                run_function(self.func, [item] + self.args, worker_outputs)
            except Exception as e:
                if not self.suppress_worker_exceptions:
                    raise e
                else:
                    LOG.info("Logging '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))
        if log_start_finish:
            LOG.info('Finished single-processed SynchronousJob...')
        return worker_outputs

    def run_multi_processed(self, log_start_finish=False):
        if log_start_finish:
            LOG.info('Beginning multi-processed SynchronousJob...')
        # The correct way to handle Ctrl+C/SIGINT with multiprocessing.Pool is to:
        # 1) Make the process ignore SIGINT before a process Pool is created. 
        #    This way created child processes inherit SIGINT handler.
        # 2) Restore the original SIGINT handler in the parent process after a Pool has been created.
        # 3) Wait on the results with timeout because the default "blocking-waits" ignore all signals.
        # ** Based on https://stackoverflow.com/a/35134329/3577492

        # SIGINT-handling step 1
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

        manager = Manager()
        worker_outputs = manager.list() # This will accumulate return values of 'func'.

        pool_params = {'processes':self.processes,
                       'maxtasksperchild':1} # In tandum with timeout, this implements the process timeout.
        if sys.version_info[0] < 2.7:
            pool_params.pop('maxtasksperchild')

        # SIGINT-handling step 2
        if self.no_daemon:
            pool = NoDaemonProcessPool(**pool_params)
        else:
            pool = Pool(**pool_params)
        signal.signal(signal.SIGINT, original_sigint_handler)

        worker_statuses = [] # A list of AsyncResult's.
        for item in self.items:
            worker_statuses.append(pool.apply_async(run_function, [self.func, [item] + self.args, worker_outputs]))
        pool.close() # no more work will be submitted to workers

        for ws in worker_statuses:
            try:
                # SIGINT-handling step 3
                ws.get(self.timeout)  # checks for worker errors
            except KeyboardInterrupt:
                LOG.info('caught KeyboardInterrupt, terminating workers')
                pool.terminate()
                raise
            except Exception as e:
                if not self.suppress_worker_exceptions:
                    pool.terminate()
                    raise e
                else:
                    LOG.info("Logging '%s:%s' but neglecting to raise it" % (e.__class__.__name__, e.message))

        pool.join() # wait for worker processes to terminate
        if log_start_finish:
            LOG.info('Finished multi-processed SynchronousJob...')
        return list(worker_outputs)

def run_function(some_function, args, worker_outputs):
    """This is a method that will be called by every SynchronousJob worker.
        Args:
            some_function (function): The function that will be applied to 'args'.
            args (list): The complete list of args that supplies some_function's signature.
            worker_outputs (list): The return values of any given some_function result appeneded to this list.
    
        Notes:
            - Stacktraces from exceptions are logged so users can see exactly why a worker failed.
            - Multiprocess note: worker_outputs is a multiprocessing.managers.ListProxy for multi_processed SynchronousJob runs.
    """
    try:
        output = some_function(*args)
        worker_outputs.append(output)
    except Exception as e:
        worker_outputs.append(None)
        stacktrace = traceback.format_exc()
        LOG.error(stacktrace)
        raise e
