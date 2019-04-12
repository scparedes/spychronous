# spychronous
A simple synchronous job runner for parallel processing tasks.

## spychronous in action
TL;DR Here's a quick example:
```python
from spychronous import SynchronousJob as Job

def get_plus_one(num):
    return num + 1

nums = [1, 2, 3]
plus_one_job = Job(func=get_plus_one, items=nums)

print plus_one_job.run_multi_processed()
# OUTPUT
# [2, 3, 4]
```
## Working with spychronous
Say you've written a function that will be repeatedly called to transform a list:
```python
>>> def get_plus_one(item):
...     return item + 1
...
>>> items = [1, 2, 3]
>>> for item in items:
...     get_plus_one(item)
...
2
3
4
```
Using a spychronous `Job` instead, you can _parallel process_ the list-transformation (and repeatedly apply your function to each item in your list):
```python
>>> from spychronous import SynchronousJob as Job
>>> plus_one_job = Job(func=get_plus_one, items=items)
>>> plus_one_job.run_multi_processed()
[2, 3, 4]
```
Now imagine your function changes to require _more_ arguments than simply an item from your list, like a `multiplier`:
``` python
>>> from time import sleep
>>> from random import random
>>> 
>>> def get_number(item, multiplier):
...    sleep(random()*5) # your function executes at variable speed
...    return item * multiplier
```
_Notice the first parameter will hold a single `item` from `Job`'s `items` and additional parameters (like `multiplier`) are listed in the signature afterwards._

`Job` accounts for this by using `args`:
``` python
>>>	multiplier = 2
>>>	additional_function_args = [multiplier]
>>>	numbers_job = Job(func=get_number, items=items, args=additional_function_args)
>>>	numbers_job.run_multi_processed()
[8, 4, 6]
```
_Notice there's no guaranteed order of the output. See [Coupling output to input](#coupling-output-to-input) for tips on working with this behavior._
#### Important Configurable Features
If you need to set process pool size, set worker timeouts, handle Ctrl-C, or run your job single-processed (to debug, for instance), the following features come in handy.
###### Process Pool Size
```python
Job(...processes=20) # default is 4
```
###### Worker Timeouts
```python
minutes = 60
Job(...timeout=5*minutes)
```
###### Non-Daemonic Process Pool
The default `multiprocessing.pool.Pool` disallows spawning processes within processes.  This can be properly circumvented with the `no_daemon` attribute.
```python
Job(...no_daemon=True)
```
###### Child-Exception Suppression
If you don't want a `Job`'s children (i.e. workers) to die if another raises an exception i.e. you want remaining items in your list to be processed, you can suppress those exceptions and log them instead.
```python
Job(...suppress_worker_exceptions=True)
```
###### Predictable Ctrl-C Handling
`Job` also handles `SIGINT` gracefully by intentionally killing its workers ASAP, and then killing itself afterwards:
```python
>>> from time import sleep, strftime, gmtime
>>> from random import random
>>> def print_item(item):
...     sleep(random()*50)
...     print strftime("%H:%M:%S", gmtime()), item
...
>>> printing_job = Job(func=print_item, items=items)
>>> items = [1, 2, 3]
>>> # GOAL: print the following: 1) item and item's timestamp 2) Ctrl-C's timestamp
>>> try:
...     printing_job.run_multi_processed()
... finally:
...     from time import gmtime, strftime, sleep
...     print '', strftime("%H:%M:%S", gmtime()), 'user issued Ctrl-C'
...
20:39:50 3
20:39:52 1
^C 20:41:53 user issued Ctrl-C
Traceback (most recent call last):
... Your typical stacktrace here ...
KeyboardInterrupt
```
###### Run Job with Single Process (for dev-ing, debugging, etc.)
When you plan to parallelize a job, it's helpful to develop with single-processed job execution first (and debug likewise) and then switch to multi-processed job execution when you're ready.  The spychronous `Job` can facilitate this with the `run_single_processed` instance method.

_Utilizing run_single_processed: A Use Case..._

* The following example illustrates the aforementioned proposal for development, debugging, and deployment with `run_single_processed`.
* Illustrated using 3 different iterations of the same program:
```python
# 1st iteration: Development
from spychronous import SynchronousJob as Job
def get_plus_one(num):
    return num + 1/0

nums = [1, 2, 3]
job = Job(func=get_plus_one, items=nums)
job.run_single_processed()
# OUTPUT
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
#   File "spychronous.py", line 33, in run_single_processed
#     raise e
# ZeroDivisionError: integer division or modulo by zero
```
```python
# 2nd iteration: Debugging
from spychronous import SynchronousJob as Job
def get_plus_one(num):
    import pdb;pdb.set_trace()
    return num + 1/0

nums = [1, 2, 3]
job = Job(func=get_plus_one, items=nums)
job.run_single_processed()
# OUTPUT
# <stdin>(5)get_plus_one()
# (Pdb) print item
# 3
```
```python
# 3rd iteration: Multiprocessing the Job
from spychronous import SynchronousJob as Job
def get_plus_one(num):
    return num

nums = [1, 2, 3]
job = Job(func=get_plus_one, items=nums)
job.run_multi_processed() # notice method name changed from 'single' to 'multi'
# OUTPUT
# [1, 3, 2]
```

#### Working with instance methods
In order to call an instance method on a list of objects, simply wrap the instance method call in a trivial method:
```python
>>> class Cat(object):
...     def __init__(self, name):
...         self.name = name
...     def meow(self):
...         print 'meow, my name is', self.name
... 
>>> def make_cat_meow(cat):
...     cat.meow()
...
>>> dave = Cat('Dave')
>>> meow_job = Job(func=make_cat_meow, items=[dave])
>>> meow_job.run_multi_processed()
meow, my name is Dave
```

#### Coupling output to input
In order to preserve a relationship between input and output, simply wrap your function in one that couples the IO:
```python
>>> def get_num_times_2(num):
...     return num * 2
...
>>> def double_num(num): # this is the coupling function.
... 	return (num, get_num_times_2(num))
...
>>> doubling_job = Job(func=double_num, items=[5])
>>> doubling_job.run_multi_processed()
[(5, 10)]
```

## TODO: AsynchronousJob, Thread Pools
The next step for spychronous is an asynchrounous job runner.  This is being developed in the develop branch.  After that, thread pools will be implemented as an alternative to process pools.

## Why spychronous?
I made spychronous because I wanted a clean out-of-the-box solution to quickly replace loops that I wanted to parallel process.  I wanted hide burdensome configuration and process management from the user. I wanted a solution that would gracefully handle `SIGINT`.

Lastly, it was a fun programming exercise for me.