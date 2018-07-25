import os
import sys
spychronous_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path += [spychronous_dir]
from spychronous import SynchronousJob, run_function
import unittest
import multiprocessing
import subprocess
import shlex
import signal
from time import sleep

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

    def test_worker_return_values_are_aggregated(self):
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
        
    def test_suppress_raised_worker_exceptions_and_complete_execution(self):
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

    def test_handle_sigint(self):
        child_program_name = 'run_forever.py'
        # Kill any processes with run_forever.py running.
        process_records = run_command('ps -A')
        for record in process_records:
            if child_program_name in record:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)
        # Spin up the never-self-terminating subprocess.
        python_interpreter = sys.executable # user's current python interpreter.
        run_forever_script_path = os.path.join(spychronous_dir, 'tests', 'run_forever.py')
        cmd = python_interpreter + ' ' + run_forever_script_path
        process = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE) # stderr will contain sigint -- we don't want to see it.
        # Verify that the subprocess exists and has spawned children.
        greppable_path = get_greppable(run_forever_script_path)
        exact_interpreter = run_command("ps -ef | grep '%s' | awk '{ print $8 }'" % greppable_path).splitlines()[0] # the python path could have been expanded in the subprocess.
        exact_cmd = exact_interpreter + ' ' + run_forever_script_path
        greppable_cmd = get_greppable(exact_cmd)
        parent_pid = run_command("ps -ef | grep '%s' | awk '{ print $2 }'" % greppable_cmd).splitlines()[0]
        if not parent_pid:
            process.send_signal(signal.SIGINT)
            raise Exception('No parent pid!!!')
        greppable_pid = get_greppable(parent_pid)
        children_pids = run_command("ps -ef | grep '%s' | awk '{ print $2 }' | grep -v '%s'" % (greppable_pid, greppable_pid)).splitlines()
        self.assertGreater(len(children_pids), 0)
        # Kill the subprocess.
        process.send_signal(signal.SIGINT)
        WAIT_PROCESS_DIE_SECS = 1
        sleep(WAIT_PROCESS_DIE_SECS)
        # Verify we've killed the subprocess and its children (the children's routine runs forever -- if they aren't dead, sigint didn't propogate properly).
        self.assertTrue(process.poll())
        WAIT_CHILDREN_DIE_SECS = 1
        sleep(WAIT_CHILDREN_DIE_SECS)
        children_pids = run_command("ps -ef | grep '%s' | awk '{ print $2 }' | grep -v '%s'" % (greppable_pid, greppable_pid)).splitlines()
        self.assertEqual(len(children_pids), 0)

class TestRunSingleProcessed(TestRun, unittest.TestCase):
    def setUp(self):
        super(TestRunSingleProcessed, self).setUp()
        self.instance_method_name = 'run_single_processed'

class TestRunFunction(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.input_args = [1]
        self.output_nums = [] # we collect the output and build upon it as we proceed.

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


### SIMPLE FUNCTIONS TO USE FOR TESTING ###
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

### HELPER FUNCTIONS ###
def run_command(cmd):
    if "|" in cmd:
        cmd_parts = cmd.split('|')
    else:
        cmd_parts = [cmd]
    p = {}
    for i, cmd_part in enumerate(cmd_parts):
        cmd_part = cmd_part.strip()
        if i == 0:
            p[i]=subprocess.Popen(shlex.split(cmd_part),stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p[i]=subprocess.Popen(shlex.split(cmd_part),stdin=p[i-1].stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout_data, std_error_data) = p[i].communicate()
    exit_code = p[0].wait()

    if exit_code != 0:
        print "Output:"
        print str(stdout_data)
        raise Exception(std_error_data)
    else:
        return str(stdout_data).strip()

def get_greppable(string):
    """Simply produces a string that -- when grepped -- will omit listing the grep process in a grep listing.
    """
    return string.replace(string[0], '[%s]' % string[0], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
