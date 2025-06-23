package com.challenges.datapipeline.event;

import com.challenges.datapipeline.config.RabbitConfig;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.InputStream;

@Service
public class EventProcessorService {

    private final EventRepository repository;
    private final RabbitTemplate rabbitTemplate;
    private final ObjectMapper mapper;

    public EventProcessorService(EventRepository repository, RabbitTemplate rabbitTemplate, ObjectMapper mapper) {
        this.repository = repository;
        this.rabbitTemplate = rabbitTemplate;
        this.mapper = mapper;
    }

    public void processStream(InputStream inputStream) {
        try (JsonParser parser = mapper.getFactory().createParser(inputStream)) {
            if (parser.nextToken() != JsonToken.START_ARRAY) return;

            while (parser.nextToken() == JsonToken.START_OBJECT) {
                EventDto eventDto = mapper.readValue(parser, EventDto.class);
                Event event = EventMapper.toEntity(eventDto);
                repository.save(event);
                rabbitTemplate.convertAndSend(RabbitConfig.EventQueue, eventDto);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
