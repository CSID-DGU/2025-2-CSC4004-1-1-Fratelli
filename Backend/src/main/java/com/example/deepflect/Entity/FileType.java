package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonValue;

public enum FileType {
    IMAGE("image"),
    VIDEO("video"),
    AUDIO("audio"),
    UNKNOWN("unknown");

    private final String value;

    FileType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}
