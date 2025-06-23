import multiprocessing
import queue
import time
import threading
import uuid
import heapq
from collections import defaultdict

class Task:
    def __init__(self, func, args=(), priority=0, dependencies=None, timeout=10):
        self.id = str(uuid.uuid4())
        self.func = func
        self.args = args
        self.priority = priority
        self.dependencies = dependencies if dependencies else []
        self.status = 'PENDING'
        self.result = None
        self.timeout = timeout
        self.cancelled = False

    def __lt__(self, other):
        return self.priority < other.priority

class TaskScheduler:
    def __init__(self):
        self.task_queue = []
        self.tasks = {}
        self.dependency_graph = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.completed_tasks = set()
        self.failed_tasks = set()
        self.running_tasks = {}
        self.lock = threading.Lock()
        self.manager = multiprocessing.Manager()
        self.workers = []
        self.num_workers = 2
        self.task_results = self.manager.dict()
        self.worker_pool = multiprocessing.Pool(processes=self.num_workers)

    def add_task(self, task):
        with self.lock:
            self.tasks[task.id] = task
            if not task.dependencies:
                heapq.heappush(self.task_queue, task)
            else:
                for dep in task.dependencies:
                    self.dependency_graph[task.id].add(dep)
                    self.reverse_dependencies[dep].add(task.id)

    def mark_completed(self, task_id, result):
        with self.lock:
            self.completed_tasks.add(task_id)
            self.tasks[task_id].status = 'COMPLETED'
            self.tasks[task_id].result = result
            for dep in self.reverse_dependencies[task_id]:
                self.dependency_graph[dep].remove(task_id)
                if not self.dependency_graph[dep]:
                    heapq.heappush(self.task_queue, self.tasks[dep])

    def mark_failed(self, task_id):
        with self.lock:
            self.failed_tasks.add(task_id)
            self.tasks[task_id].status = 'FAILED'

    def cancel_task(self, task_id):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].cancelled = True
                self.tasks[task_id].status = 'CANCELLED'

    def run_task(task, result_dict):
        try:
            if task.cancelled:
                result_dict[task.id] = ('CANCELLED', None)
            else:
                result = task.func(*task.args)
                result_dict[task.id] = ('SUCCESS', result)
        except Exception as e:
            result_dict[task.id] = ('FAILED', str(e))

    def task_runner(self, task_id):
        task = self.tasks[task_id]
        if task.cancelled:
            return

        result_dict = self.manager.dict()
        p = multiprocessing.Process(target=run_task, args=(task, result_dict))
        p.start()
        p.join(timeout=task.timeout)

        if p.is_alive():
            p.terminate()
            self.task_results[task.id] = ('TIMEOUT', None)
        else:
            self.task_results[task.id] = result_dict.get(task.id, ('FAILED', None))


    def worker_loop(self):
        while True:
            with self.lock:
                if not self.task_queue:
                    continue
                task = heapq.heappop(self.task_queue)
                if task.cancelled:
                    continue
                task.status = 'RUNNING'
                self.running_tasks[task.id] = task

            self.task_runner(task.id)
            status, result = self.task_results.get(task.id, ('FAILED', None))

            if status == 'SUCCESS':
                self.mark_completed(task.id, result)
            else:
                self.mark_failed(task.id)

            with self.lock:
                del self.running_tasks[task.id]

    def start(self):
        for _ in range(self.num_workers):
            t = threading.Thread(target=self.worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

    def scale_workers(self, count):
        self.num_workers += count
        for _ in range(count):
            t = threading.Thread(target=self.worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

    def status_report(self):
        with self.lock:
            report = {
                'PENDING': [tid for tid, t in self.tasks.items() if t.status == 'PENDING'],
                'RUNNING': list(self.running_tasks.keys()),
                'COMPLETED': list(self.completed_tasks),
                'FAILED': list(self.failed_tasks),
                'CANCELLED': [tid for tid, t in self.tasks.items() if t.status == 'CANCELLED'],
            }
        return report

# Sample usage
def example_task(x):
    time.sleep(1)
    return x * x

if __name__ == '__main__':
    scheduler = TaskScheduler()
    scheduler.start()

    # Create tasks
    t1 = Task(func=example_task, args=(2,), priority=1)
    t2 = Task(func=example_task, args=(3,), priority=2, dependencies=[t1.id])
    t3 = Task(func=example_task, args=(4,), priority=3)

    scheduler.add_task(t1)
    scheduler.add_task(t2)
    scheduler.add_task(t3)

    time.sleep(5)

    print("Status Report:", scheduler.status_report())