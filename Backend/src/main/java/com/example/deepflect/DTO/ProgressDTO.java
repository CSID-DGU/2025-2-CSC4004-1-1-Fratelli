package com.example.deepflect.DTO;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class ProgressDTO {
    private String taskId;
    private int progress;
    private String downloadUrl;
}
