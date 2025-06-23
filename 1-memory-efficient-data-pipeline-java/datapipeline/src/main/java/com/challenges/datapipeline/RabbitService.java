package com.challenges.datapipeline;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class RabbitService {

    private final RabbitTemplate rabbitTemplate;
    private final ObjectMapper objectMapper;

    public RabbitService(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
        this.objectMapper = new ObjectMapper();
    }

    public void publish(Map<String, Object> data) {
        try {
            String json = objectMapper.writeValueAsString(data);
            rabbitTemplate.convertAndSend("events", json);
        } catch (JsonProcessingException e) {
            e.printStackTrace();
        }
    }
}
