import java.util.*;
import java.util.concurrent.*;

public class Main {
    public static void main(String[] args) throws InterruptedException {
        CountDownLatch latch = new CountDownLatch(4);

        TaskScheduler scheduler = new TaskScheduler(3);
        scheduler.start();

        Task taskA = new Task(
                "A", 1, List.of(),
                () -> {
                    Thread.sleep(3000);
                    latch.countDown();
                    return null;
                });

        Task taskB = new Task(
                "B", 2, List.of("A"),
                () -> {
                    Thread.sleep(2000);
                    latch.countDown();
                    return null;
                });

        Task taskC = new Task(
                "C", 3, List.of("A", "B"),
                () -> {
                    Thread.sleep(1000);
                    latch.countDown();
                    return null;
                });

        Task taskD = new Task(
                "D", 5, List.of(),
                () -> {
                    Thread.sleep(1000);
                    latch.countDown();
                    return null;
                });

        scheduler.submitTask(taskA);
        scheduler.submitTask(taskB);
        scheduler.submitTask(taskC);
        scheduler.submitTask(taskD);

        latch.await();
        System.out.println("All tasks completed. Main thread exiting.");
    }
}