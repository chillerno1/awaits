from awaits.units.abstract_unit import AbstractUnit


class ThreadUnit(AbstractUnit):
    """
    An instance of the class corresponds to one thread. Tasks are performed here.
    """
    def __init__(self, queue, pool, index):
        self.index = index
        self.queue = queue
        self.pool = pool

    def run(self):
        """
        We accept tasks from the queue and execute them.
        """
        while True:
            try:
                task = self.queue.get()
                task.do()
                self.queue.task_done()
            except Exception as e:
                pass
