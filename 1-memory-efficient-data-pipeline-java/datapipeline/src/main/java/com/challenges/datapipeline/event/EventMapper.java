package com.challenges.datapipeline.event;

public class EventMapper {
    public static Event toEntity(EventDto dto) {
        return new Event(dto.userId(), dto.action(), dto.timestamp());
    }
}