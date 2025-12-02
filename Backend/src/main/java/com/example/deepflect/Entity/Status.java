package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonValue;

public enum Status {
    UPLOADING("uploading"),
    FAILED("fail"),
    SUCCESS("success");

    private final String value;

    Status(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}
