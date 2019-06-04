from multiprocessing import Process, pool

class NoDaemonProcess(Process):
    """A process with the deamon property set to False.
    
        Purpose: multiprocessing.pool.Pool makes processes daemonic and then immediately starts them.
                 It's not possible to re-set their daemon attribute to False before they are 
                 started and afterwards it's not allowed anymore. This circumvents that.
    """
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)
 
# We sub-class multiprocessing.pool.Pool instead of multiprocessing.Pool
# because the latter is only a wrapper function, not a proper class.
class NoDaemonProcessPool(pool.Pool):
    Process = NoDaemonProcess

# taken from https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic