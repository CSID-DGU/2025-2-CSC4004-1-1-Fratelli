package com.example.deepflect.Controller;

import com.example.deepflect.DTO.NotificationDTO;
import com.example.deepflect.DTO.NotificationListResponse;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.NotificationRepository;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.FcmService;
import com.example.deepflect.Service.NotificationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/notification")
public class NotificationController {

    @Autowired
    NotificationRepository notificationRepository;

    @Autowired
    NotificationService notificationService;

    @Autowired
    UsersRepository usersRepository;

    @Autowired
    FcmService fcmService;

    /**
     * 알림 목록 확인
     * GET /api/v1/notification/myNotification
     */
    @GetMapping("/myNotification")
    public ResponseEntity<NotificationListResponse> getMyNotifications() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String userEmail = authentication.getName();
        
        List<NotificationDTO> notifications = notificationService.getNotificationsByUser(userEmail);
        
        NotificationListResponse response = new NotificationListResponse();
        response.setNotifications(notifications);
        
        return ResponseEntity.ok(response);
    }

    @GetMapping("/myNotification/{notificationId}")
    public ResponseEntity<String> getNotification(@PathVariable("notificationId") Long notificationId) {
        try {
            notificationService.deleteNotification(notificationId);
            return ResponseEntity.ok("OK");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete notification");
        }
    }

    /**
     * 알림 삭제
     * DELETE /api/v1/notification/myNotification/{id}
     */
    @DeleteMapping("/myNotification/{notificationId}")
    public ResponseEntity<String> deleteNotification(@PathVariable("notificationId") Long notificationId) {
        try {
            notificationService.deleteNotification(notificationId);
            return ResponseEntity.ok("OK");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete notification");
        }
    }

    @PostMapping("/send")
    public ResponseEntity<?> send(
            @RequestParam("email") String email,
            @RequestParam("title") String title,
            @RequestParam("body") String body
    ) {
        Users user = usersRepository.findByEmail(email)
                .orElse(null);

        if (user == null) {
            return ResponseEntity.badRequest().body("User not found");
        }

        fcmService.sendNotificationToUser(user, title, body);

        return ResponseEntity.ok("Notification Sent");
    }

}
