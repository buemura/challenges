package com.challenges.datapipeline;



import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;

@RestController
@RequestMapping("/webhook")
public class WebhookController {

    private final BlockingQueue<Map<String, Object>> inputQueue = new LinkedBlockingQueue<>(10000);
    private final ObjectMapper objectMapper = new ObjectMapper();

    private final DatabaseService dbService;
    private final RabbitService rabbitService;

    public WebhookController(DatabaseService dbService, RabbitService rabbitService) {
        this.dbService = dbService;
        this.rabbitService = rabbitService;

        // Start aggregator background task
        startAggregator();
    }

    @PostMapping
    public Mono<Map<String, Object>> receive(@RequestBody Mono<String> body) {
        return body.flatMap(json -> {
            try {
                JsonNode rootNode = objectMapper.readTree(json);
                List<Map<String, Object>> items = new ArrayList<>();

                if (rootNode.isObject()) {
                    items.add(objectMapper.convertValue(rootNode, new TypeReference<>() {}));
                } else if (rootNode.isArray()) {
                    for (JsonNode node : rootNode) {
                        items.add(objectMapper.convertValue(node, new TypeReference<>() {}));
                    }
                }

                items.forEach(inputQueue::offer);

                Map<String, Object> response = Map.of("status", "queued", "received", items.size());
                return Mono.just(response);
            } catch (IOException e) {
                return Mono.error(new RuntimeException("Invalid JSON", e));
            }
        });
    }

    private void startAggregator() {
        Executors.newSingleThreadExecutor().submit(() -> {
            Map<String, Integer> userActionCount = new HashMap<>();
            while (true) {
                try {
                    Map<String, Object> event = inputQueue.take();

                    String userId = (String) event.get("user_id");
                    int count = userActionCount.getOrDefault(userId, 0) + 1;
                    userActionCount.put(userId, count);
                    event.put("action_count", count);

                    dbService.writeToDb(event).subscribe();
                    rabbitService.publish(event);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }
}