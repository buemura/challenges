package com.challenges.datapipeline.event;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.io.Serializable;
import java.time.Instant;

public record EventDto(
        @JsonProperty("user_id") int userId,
        String action,
        Instant timestamp
) implements Serializable {}