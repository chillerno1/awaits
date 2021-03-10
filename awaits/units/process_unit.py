from awaits.units.abstract_unit import AbstractUnit


class ProcessUnit(AbstractUnit):
    """
    An instance of the class corresponds to one thread. Tasks are performed here.
    """
    def __init__(self, queue, index):
        self.index = index
        self.queue = queue
        #self.pool = pool

    def run(self):
        """
        We accept tasks from the queue and execute them.
        """
        while True:
            try:
                subtask = self.queue.get_nowait()
                #module = __import__(subtask['module'])
                #func = getattr(module, subtask['function'] + '2')
                print(subtask)
                #func(*(subtask['args']), **(subtask['kwargs']))
            except Exception as e:
                pass
