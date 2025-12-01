package com.example.deepflect.DTO;

import com.example.deepflect.Entity.Notification;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
@NoArgsConstructor
public class NotificationDTO {
    private Long notificationId;
    private String taskId;
    private String status;
    private String fileName;
    private String fileType;
    private String message;
    private String timestamp;

    // id 전용 생성자
    public NotificationDTO(Long id) {
        this.notificationId = id;
    }

}
