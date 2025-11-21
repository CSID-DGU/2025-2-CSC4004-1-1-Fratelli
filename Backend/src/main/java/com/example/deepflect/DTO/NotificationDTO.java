package com.example.deepflect.DTO;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
@NoArgsConstructor
public class NotificationDTO {
    private String taskId;
    private String status;
    private String fileName;
    private String fileType;
    private String message;
    private String timestamp;
}
