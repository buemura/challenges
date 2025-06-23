package com.challenges.datapipeline;

import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.Map;

@Service
public class DatabaseService {

    private final DatabaseClient databaseClient;

    public DatabaseService(DatabaseClient databaseClient) {
        this.databaseClient = databaseClient;
    }

    public Mono<Void> writeToDb(Map<String, Object> event) {
        LocalDateTime timestamp = LocalDateTime.parse(((String) event.get("timestamp")).replace("Z", ""));
        return databaseClient.sql("INSERT INTO events(user_id, action, timestamp) VALUES(:userId, :action, :timestamp)")
                .bind("userId", event.get("user_id"))
                .bind("action", event.get("action"))
                .bind("timestamp", timestamp)
                .then();
    }
}
