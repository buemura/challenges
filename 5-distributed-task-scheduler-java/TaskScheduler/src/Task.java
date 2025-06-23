import java.util.List;
import java.util.concurrent.Callable;

public class Task implements Comparable<Task> {
    public String id;
    public int priority;
    public List<String> dependencies;
    public Callable<Void> job;

    public Task(String id, int priority, List<String> dependencies, Callable<Void> job) {
        this.id = id;
        this.priority = priority;
        this.dependencies = dependencies;
        this.job = job;
    }

    @Override
    public int compareTo(Task other) {
        return Integer.compare(other.priority, this.priority);
    }
}