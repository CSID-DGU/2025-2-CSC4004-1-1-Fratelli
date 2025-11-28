package com.example.deepflect.DTO;

import lombok.Data;

@Data
public class ProgressRequest {
    private String taskId;
    private int progress;
    private String progressStatus;
}
