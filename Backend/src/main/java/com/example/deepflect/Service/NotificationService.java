package com.example.deepflect.Service;

import com.example.deepflect.DTO.NotificationDTO;
import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Notification;
import com.example.deepflect.Entity.Status;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.NotificationRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class NotificationService {

    @Autowired
    NotificationRepository notificationRepository;

    /**
     * 알림 생성 (파일 변환 완료/실패 시 호출)
     */
    public void createNotification(Users user, String taskId, Status status, 
                                   String fileName, FileType fileType, String message) {
        Notification notification = new Notification();
        notification.setUser(user);
        notification.setTaskId(taskId);
        notification.setStatus(status);
        notification.setFileName(fileName);
        notification.setFileType(fileType);
        notification.setMessage(message);
        notification.setTimestamp(new Timestamp(System.currentTimeMillis()));
        
        notificationRepository.save(notification);
    }

    /**
     * 사용자의 알림 목록 조회
     */
    public List<NotificationDTO> getNotificationsByUser(String userEmail) {
        List<Notification> notifications = notificationRepository.findByUserEmailOrderByTimestampDesc(userEmail);
        
        return notifications.stream()
            .map(this::convertToDTO)
            .collect(Collectors.toList());
    }

    /**
     * 알림 삭제
     */
    public void deleteNotification(Long notificationId) {
        notificationRepository.deleteById(notificationId);
    }

    /**
     * Entity -> DTO 변환
     */
    private NotificationDTO convertToDTO(Notification notification) {
        NotificationDTO dto = new NotificationDTO();
        dto.setTaskId(notification.getTaskId());
        dto.setStatus(notification.getStatus() != null ? notification.getStatus().getValue() : "");
        dto.setFileName(notification.getFileName() != null ? notification.getFileName() : "");
        dto.setFileType(notification.getFileType() != null ? notification.getFileType().getValue() : "");
        dto.setMessage(notification.getMessage() != null ? notification.getMessage() : "");
        
        // Timestamp를 ISO 8601 형식으로 변환
        if (notification.getTimestamp() != null) {
            ZonedDateTime zdt = notification.getTimestamp()
                .toInstant()
                .atZone(ZoneId.systemDefault());
            dto.setTimestamp(zdt.format(DateTimeFormatter.ISO_OFFSET_DATE_TIME));
        } else {
            dto.setTimestamp("");
        }
        
        return dto;
    }

    /**
     * 기존 메서드 유지 (호환성)
     */
    public void sendNotification(Users users, String message) {
        Notification notification = new Notification(users, message);
        notificationRepository.save(notification);
    }
}
