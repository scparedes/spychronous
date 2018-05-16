import os
import sys
spychronous_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path += [spychronous_dir]
from spychronous import SynchronousJob, run_function
import unittest
import multiprocessing

import logging
logger = logging.getLogger('spychronous')
logger.disabled = True

class TestRun(object):
    maxDiff = None

    def setUp(self):
        self.addend = 2
        self.items = [1,2,3]
        self.items_without_3 = [i != 3 and i or None for i in self.items]
        self.instance_method_name = None

    def test_worker_return_values_collected(self):
        plus_num_job = SynchronousJob(func=get_plus_num, items=self.items, args=[self.addend])
        new_items = getattr(plus_num_job, self.instance_method_name)()
        items_plus_addend = map(lambda i: i+self.addend, self.items)
        self.assertEqual(new_items, items_plus_addend)

        # test that no values are collected when SynchronousJob fails.
        zero_div_error_job = SynchronousJob(func=perform_ZeroDivisionError, items=self.items)
        with self.assertRaises(ZeroDivisionError):
            output = getattr(zero_div_error_job, self.instance_method_name)()
        with self.assertRaises(UnboundLocalError): # output was never able to be defined.
            output

        # test outputs are collected when worker exceptions aren't raised.
        allowing_number_except_3_job = SynchronousJob(func=get_number_except_perform_ZeroDivisionError_on_3, items=self.items, suppress_worker_exceptions=True)
        output = getattr(allowing_number_except_3_job, self.instance_method_name)()
        self.assertEqual(output, self.items_without_3)
        
    def test_suppress_raised_worker_exceptions(self):
        # testing the opposite first.
        zero_div_error_job = SynchronousJob(func=perform_ZeroDivisionError, items=self.items, suppress_worker_exceptions=False)
        with self.assertRaises(ZeroDivisionError):
            getattr(zero_div_error_job, self.instance_method_name)()

        # testing correct behavior.
        zero_div_error_job = SynchronousJob(func=get_number_except_perform_ZeroDivisionError_on_3, items=self.items, suppress_worker_exceptions=True)
        output = getattr(zero_div_error_job, self.instance_method_name)()
        self.assertEqual(output, self.items_without_3)

class TestRunMultiProcessed(TestRun, unittest.TestCase):
    def setUp(self):
        super(TestRunMultiProcessed, self).setUp()
        self.instance_method_name = 'run_multi_processed'

    # def test_handle_sigint(self):
    #     this_pid = os.getpid()
    #     sleeping_job = SynchronousJob(func=sleep_and_get_item, items=self.items)

    #     from multiprocessing import Pool
    #     pool = Pool(processes=1)
    #     result = pool.apply_async(kill_process, args=(this_pid,), callback=do_nothing)
    #     # result.get()
    #     output = sleeping_job.run_multi_processed()
    #     print 'sleeping_job overrrr!!!'


class TestRunSingleProcessed(TestRun, unittest.TestCase):
    def setUp(self):
        super(TestRunSingleProcessed, self).setUp()
        self.instance_method_name = 'run_single_processed'

class TestRunFunction(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.input_args = [1]
        self.output_nums = [] # we'll collect the output and build upon it as we proceed.

    def test_run_function(self):
        input_args = self.input_args
        output_nums = self.output_nums
        run_function(get_plus_one, input_args, output_nums)
        self.assertEqual(output_nums, [2])

        input_args = [5]
        run_function(get_plus_one, input_args, output_nums)
        self.assertEqual(output_nums, [2, 6])

        with self.assertRaises(ZeroDivisionError):
            run_function(perform_ZeroDivisionError, input_args, output_nums)
        self.assertEqual(output_nums, [2, 6, None])



### SIMPLE USELESS FUNCTIONS TO USE FOR TESTING ###
def get_plus_one(number):
    return number + 1

def get_plus_num(number1, number2):
    return number1 + number2

def perform_ZeroDivisionError(number):
    1/0

def get_number_except_perform_ZeroDivisionError_on_3(number):
    if number == 3:
        perform_ZeroDivisionError(number)
    return number

def sleep_and_get_item(item):
    print 'I begin to sleep'
    from time import sleep
    sleep(1000)
    return item

def kill_process(pid):
    print 'I\'m about to kill'
    from time import sleep
    import signal
    def signal_handler(signal, frame):
            print('You pressed Ctrl+C!')
    signal.signal(signal.SIGINT, signal_handler)
    sleep(3)
    os.kill(pid,signal.SIGINT)

def do_nothing(pid):
    print 'nothing!'

if __name__ == '__main__':
    unittest.main(verbosity=2)
