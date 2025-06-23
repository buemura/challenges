package com.challenges.datapipeline.event;

import jakarta.persistence.*;

import java.time.Instant;

@Entity
public class Event {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private int userId;
    private String action;

    @Column(columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private Instant timestamp;

    public Event() {}

    public Event(int userId, String action, Instant timestamp) {
        this.userId = userId;
        this.action = action;
        this.timestamp = timestamp;
    }
}