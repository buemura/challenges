import multiprocessing
import queue
import threading
import time
import heapq
import uuid


class Task:
    def __init__(self, func, priority=0, dependencies=None, timeout=None):
        self.id = str(uuid.uuid4())
        self.func = func
        self.priority = priority
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.status = 'pending'
        self.result = None
        self.error = None

    def __lt__(self, other):
        return self.priority < other.priority


class TaskQueueManager:
    def __init__(self):
        self.task_queue = []
        self.task_map = {}
        self.completed_tasks = set()
        self.lock = threading.Lock()

    def add_task(self, task: Task):
        with self.lock:
            self.task_map[task.id] = task
            if not task.dependencies:
                heapq.heappush(self.task_queue, task)

    def get_next_task(self):
        with self.lock:
            ready_tasks = []
            while self.task_queue:
                task = heapq.heappop(self.task_queue)
                if all(dep_id in self.completed_tasks for dep_id in task.dependencies):
                    task.status = 'running'
                    return task  # Return the first ready task
                else:
                    ready_tasks.append(task)
            # Push back all tasks we skipped
            for task in ready_tasks:
                heapq.heappush(self.task_queue, task)
        return None

    def mark_complete(self, task, result=None):
        with self.lock:
            task.status = 'success'
            task.result = result
            self.completed_tasks.add(task.id)

    def mark_failed(self, task, error=None):
        with self.lock:
            task.status = 'failed'
            task.error = error


class Worker(multiprocessing.Process):
    def __init__(self, task_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue):
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        while True:
            try:
                task_data = self.task_queue.get(timeout=3)
                if task_data == 'STOP':
                    break
                task_id, func = task_data
                try:
                    result = func()
                    self.result_queue.put(('success', task_id, result))
                except Exception as e:
                    self.result_queue.put(('failed', task_id, str(e)))
            except queue.Empty:
                continue


class Scheduler:
    def __init__(self, num_workers=2):
        self.manager = TaskQueueManager()
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.workers = []
        for _ in range(num_workers):
            worker = Worker(self.task_queue, self.result_queue)
            worker.start()
            self.workers.append(worker)

    def submit_task(self, task):
        self.manager.add_task(task)

    def schedule(self):
        def monitor():
            while True:
                # Process results first
                try:
                    while True:
                        status, task_id, data = self.result_queue.get_nowait()
                        task = self.manager.task_map.get(task_id)
                        if not task:
                            continue
                        if status == 'success':
                            self.manager.mark_complete(task, data)
                            print(f"[✓] Task {task.id} completed with result: {data}")
                        else:
                            self.manager.mark_failed(task, data)
                            print(f"[✗] Task {task.id} failed with error: {data}")
                except queue.Empty:
                    pass

                # Dispatch any task that's ready
                task = self.manager.get_next_task()
                if task:
                    print(f"Dispatching task {task.id} with priority {task.priority}")
                    self.task_queue.put((task.id, task.func))

                time.sleep(0.1)

        threading.Thread(target=monitor, daemon=True).start()

    def wait_for_all(self, timeout=None):
        start = time.time()
        while True:
            all_done = all(task.status in ['success', 'failed'] for task in self.manager.task_map.values())
            if all_done:
                break
            if timeout and (time.time() - start > timeout):
                print("Timeout waiting for all tasks.")
                break
            time.sleep(0.1)

    def stop(self):
        for _ in self.workers:
            self.task_queue.put('STOP')
        for w in self.workers:
            w.join()

        print("\nFinal Task States:")
        for task in self.manager.task_map.values():
            print(f"Task {task.id} [{task.status}] -> {task.result or task.error}")


def sample_task():
    time.sleep(1)
    return "done"


# Example usage
if __name__ == '__main__':
    multiprocessing.set_start_method("spawn")

    scheduler = Scheduler(num_workers=3)
    scheduler.schedule()

    t1 = Task(sample_task, priority=1)
    t2 = Task(sample_task, priority=2, dependencies=[t1.id])
    scheduler.submit_task(t1)
    scheduler.submit_task(t2)

    scheduler.wait_for_all(timeout=10)
    scheduler.stop()
