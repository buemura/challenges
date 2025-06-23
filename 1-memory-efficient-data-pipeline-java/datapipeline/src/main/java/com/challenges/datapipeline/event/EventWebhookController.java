package com.challenges.datapipeline.event;


import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.InputStream;


@RestController
@RequestMapping("webhook")
public class EventWebhookController {

    private final EventProcessorService processor;

    public EventWebhookController(EventProcessorService processor) {
        this.processor = processor;
    }

    @PostMapping
    public ResponseEntity<Void> receiveEvents(InputStream requestBody) {
        processor.processStream(requestBody);
        return ResponseEntity.accepted().build();
    }
}