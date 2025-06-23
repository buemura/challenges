package com.challenges.datapipeline.event;

import jakarta.persistence.*;

import java.time.Instant;

@Entity
public class Event {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;

    public int userId;
    public String action;

    @Column(columnDefinition = "TIMESTAMP WITH TIME ZONE")
    public Instant timestamp;

    public Event(int userId, String action, Instant timestamp) {
        this.userId = userId;
        this.action = action;
        this.timestamp = timestamp;
    }
}