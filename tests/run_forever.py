import os
import sys
spychronous_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path += [spychronous_dir]
from spychronous import SynchronousJob

import logging
logger = logging.getLogger('spychronous')
logger.disabled = True

def run_forever_with_item(item):
    while True:
        pass
    return item

if __name__ == '__main__':
    items = [1, 2, 3]
    running_forever_job = SynchronousJob(func=run_forever_with_item, items=items)
    running_forever_job.run_multi_processed()
    print 'we will never get here'