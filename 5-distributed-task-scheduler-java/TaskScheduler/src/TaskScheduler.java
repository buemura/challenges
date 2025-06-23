import java.util.*;
import java.util.concurrent.*;

public class TaskScheduler {
    private final ExecutorService executor;
    private final PriorityBlockingQueue<Task> queue = new PriorityBlockingQueue<>();
    private final Map<String, Task> taskMap = new ConcurrentHashMap<>();
    private final Set<String> completedTasks = ConcurrentHashMap.newKeySet();

    public TaskScheduler(int workerCount) {
        this.executor = Executors.newFixedThreadPool(workerCount);
    }

    public void submitTask(Task task) {
        taskMap.put(task.id, task);
        queue.offer(task);
    }

    public void start() {
        Thread dispatcher = new Thread(() -> {
            while (true) {
                try {
                    Task task = queue.take();

                    if (!dependenciesMet(task)) {
                        queue.offer(task);
                        Thread.sleep(200);
                        continue;
                    }

                    executor.submit(() -> {
                        try {
                            System.out.println("Running Task " + task.id);
                            task.job.call();
                            completedTasks.add(task.id);
                            System.out.println("Task " + task.id + " completed");
                        } catch (Exception e) {
                            System.out.println("Task " + task.id + " failed: " + e.getMessage());
                        }
                    });

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
        dispatcher.setDaemon(true);
        dispatcher.start();
    }

    private boolean dependenciesMet(Task task) {
        return task.dependencies.stream().allMatch(completedTasks::contains);
    }
}