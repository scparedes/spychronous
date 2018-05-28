from multiprocessing import Process
from multiprocessing.managers import BaseManager
from Queue import Queue

class WorkerOutputs(object):
    """Container for collecting the output from spychronous workers.
    
        Purpose: Give the user a more robust experience with workers.
    """
    def add(self, output):
        raise NotImplementedError

class SingleProcessedWorkerOutputs(WorkerOutputs, list):
    def __init__(self):
        super(SingleProcessedWorkerOutputs, self).__init__()

    def add(self, output):
        self.append(output)

class WorkerListClass(list, WorkerOutputs):
    def __init__(self):
        super(WorkerListClass, self).__init__()

    def add(self, output):
        self.append(output)

class WorkerListManager(BaseManager):
    pass
WorkerListManager.register('MultiProcessedSynchronousWorkerOutputs', WorkerListClass)

# class MultiProcessedAsynchronousWorkerOutputs(WorkerOutputs):
#     def __init__(self):
#         super(MultiProcessedAsynchronousWorkerOutputs, self).__init__()
#         self.all_outputs = []

#     def add(self, output):
#         self.outputs.put(output)

#     def __iter__(self):
#         while True:
#             try:
#                yield self.outputs.get_nowait()
#             except Queue.Empty:
#                return

#     @property
#     def empty(self):
#         return self.outputs.empty()

#     @property
#     def output_container(self):
#         self.manager = Manager()
#         return self.manager.Queue()