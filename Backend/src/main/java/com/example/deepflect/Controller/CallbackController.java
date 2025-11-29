package com.example.deepflect.Controller;

import com.example.deepflect.DTO.FileUploadResponse;
import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Status;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping("/api/v1/callback")
public class CallbackController {

    @Autowired
    ProgressManager progressManager;

    @Autowired
    ProgressService progressService;
    
    @Autowired
    DownloadService downloadService;

    @Autowired
    UploadProgressService uploadProgressService;

    @Autowired
    NotificationService notificationService;

    @Autowired
    UsersRepository usersRepository;

    @PostMapping("/ai_progress")
    public ResponseEntity<?> aiProgress(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_progress received: taskId=" + dto.getTaskId() + " progress=" + dto.getProgress() + " progressStatus=" + dto.getProgressStatus());
        // update in-memory progress map for polling
        progressService.updateProgress(dto.getTaskId(), dto.getProgress(), dto.getProgressStatus());
        // push to any SSE listeners
        progressManager.updateProgress(dto.getTaskId(), dto.getProgress(), dto.getProgressStatus());
        return ResponseEntity.ok("received");
    }

    @PostMapping("/ai_finished")
    public ResponseEntity<?> aiFinished(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_finished received: taskId=" + dto.getTaskId());
        // mark complete for polling and SSE
        progressService.updateProgress(dto.getTaskId(), 100, "완료");
        progressManager.finish(dto.getTaskId());
        // save download URL for later retrieval
        if (dto.getDownloadUrl() != null && !dto.getDownloadUrl().isEmpty()) {
            downloadService.saveDownloadUrl(dto.getTaskId(), dto.getDownloadUrl());
        }

        // 알림 생성
//        createNotificationForTask(dto.getTaskId(), Status.SUCCESS, "Upload and noise insertion completed");
        createNotificationForTask(dto.getTaskId(), Status.SUCCESS, "파일 보호 처리가 완료되었습니다.");

        return ResponseEntity.ok("finished");
    }
    
    @PostMapping("/ai_failed")
    public ResponseEntity<?> aiFailed(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_failed received: taskId=" + dto.getTaskId());
        // mark as failed
        progressService.markFailed(dto.getTaskId());
        progressManager.finish(dto.getTaskId());

        // 알림 생성
        String message = dto.getMessage() != null && !dto.getMessage().isEmpty() 
            ? "Noise insertion failed: " + dto.getMessage() 
            : "Noise insertion failed";
        createNotificationForTask(dto.getTaskId(), Status.FAILED, message);

        return ResponseEntity.ok("failed");
    }

    /**
     * 작업 완료/실패 시 알림 생성
     */
    private void createNotificationForTask(String taskId, Status status, String message) {
        try {
            // uploadProgressService에서 업로드 메타 정보 가져오기
            FileUploadResponse uploadMeta = uploadProgressService.getUpload(taskId);
            if (uploadMeta == null) {
                System.out.println("[CallbackController] Upload metadata not found for taskId: " + taskId);
                return;
            }

            // 사용자 찾기
            String userEmail = uploadMeta.getUserEmail();
            if (userEmail == null || userEmail.isEmpty()) {
                System.out.println("[CallbackController] User email not found in upload metadata");
                return;
            }

            Users user = usersRepository.findByEmail(userEmail).orElse(null);
            if (user == null) {
                System.out.println("[CallbackController] User not found for email: " + userEmail);
                return;
            }

            // 알림 생성
            notificationService.createNotification(
                user,
                taskId,
                status,
                uploadMeta.getFileName(),
                uploadMeta.getFileType(),
                message
            );

            System.out.println("[CallbackController] Notification created for taskId: " + taskId + ", user: " + userEmail);
        } catch (Exception e) {
            System.err.println("[CallbackController] Failed to create notification: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
