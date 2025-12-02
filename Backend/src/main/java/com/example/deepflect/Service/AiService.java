package com.example.deepflect.Service;

import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Files;
import com.example.deepflect.Entity.Status;
import com.example.deepflect.Entity.Users;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class AiService {

    private static final Logger logger = LoggerFactory.getLogger(AiService.class);

    @Value("${ai.server.url}")
    private String aiServerUrl;

    @Autowired
    RestTemplate restTemplate;

    @Autowired
    NotificationService notificationService;

    /**
     * Python 음성 보호 API 호출
     * @param taskId 작업 ID
     * @param filePath 저장된 원본 파일 경로
     */
    public void requestNoiseProcessing(Users user, String taskId, String filePath) {
        String fileTypeString = "other";
        FileType fileTypeEnum = FileType.UNKNOWN; // NotificationService용 Enum

        // Add fileType hint to let Python server decide pipeline (image/video/audio)
        String lower = filePath.toLowerCase();
        if (lower.endsWith(".mp4") || lower.endsWith(".mov") || lower.endsWith(".mkv") || lower.endsWith(".avi")) {
            fileTypeString = "video";
            fileTypeEnum = FileType.VIDEO;
        } else if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".bmp") || lower.endsWith(".gif")) {
            fileTypeString = "image";
            fileTypeEnum = FileType.IMAGE;
        } else if (lower.endsWith(".wav") || lower.endsWith(".mp3") || lower.endsWith(".flac")) {
            fileTypeString = "audio";
            fileTypeEnum = FileType.AUDIO;
        }

        try {
            logger.info("[{}] Sending audio to protection service", taskId);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new FileSystemResource(new File(filePath)));

            body.add("fileType", fileTypeString);
            body.add("taskId", taskId);  // Pass backend taskId to AI

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> requestEntity =
                    new HttpEntity<>(body, headers);

            // Use unified processing endpoint with taskId parameter
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    aiServerUrl + "/api/v1/process-file?taskId=" + taskId,
                    requestEntity,
                    Map.class
            );

            logger.info("[{}] Protection response: {}", taskId, response.getBody());

            // [추가] 성공 알림 발송 (200 OK 인 경우)
//            if (response.getStatusCode().is2xxSuccessful()) {
//                notificationService.createNotification(
//                        user,
//                        taskId,
//                        Status.SUCCESS,
//                        taskId + "_protected", // 결과 파일명 예시
//                        fileTypeEnum,
//                        "AI 보호 처리가 완료되었습니다."
//                );
//            }
        }
        catch (Exception e) {
            logger.error("[{}] Error calling protection service", taskId, e);
            // [추가] 실패 알림 발송
//            notificationService.createNotification(
//                    user,
//                    taskId,
//                    Status.FAILED,
//                    taskId + "_original",
//                    fileTypeEnum,
//                    "AI 처리 중 오류가 발생했습니다."
//            );
            throw new RuntimeException("Failed to protect audio: " + e.getMessage());
        }
    }

    /**
     * 보호된 음성 다운로드
     */
    public byte[] downloadProtectedAudio(String taskId) {
        try {
            logger.info("[{}] Downloading protected audio", taskId);

            ResponseEntity<byte[]> response = restTemplate.getForEntity(
                    aiServerUrl + "/api/v1/download/" + taskId,
                    byte[].class
            );

            return response.getBody();

        } catch (Exception e) {
            logger.error("[{}] Error downloading protected audio", taskId, e);
            throw new RuntimeException("Failed to download audio: " + e.getMessage());
        }
    }

    /**
     * 작업 상태 조회
     */
    public Map<String, Object> getProtectionStatus(String taskId) {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                    aiServerUrl + "/api/v1/status/" + taskId,
                    Map.class
            );

            return response.getBody();

        } catch (Exception e) {
            logger.error("[{}] Error getting protection status", taskId, e);
            throw new RuntimeException("Failed to get status: " + e.getMessage());
        }
    }

    /**
     * 서버 헬스 체크
     */
    public boolean isAiServerHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                    aiServerUrl + "/health",
                    Map.class
            );

            return response.getStatusCode().is2xxSuccessful();

        } catch (Exception e) {
            logger.error("AI server health check failed", e);
            return false;
        }
    }

    /**
     * 처리 중인 작업 취소
     * @param taskId 작업 ID
     */
    public void cancelProcessing(String taskId) {
        try {
            logger.info("[{}] Requesting cancellation from AI server", taskId);

            restTemplate.delete(aiServerUrl + "/api/v1/cancel/" + taskId);

            logger.info("[{}] Cancellation request sent successfully", taskId);

        } catch (Exception e) {
            logger.error("[{}] Error cancelling processing", taskId, e);
            // 에러가 나도 계속 진행 (AI 서버가 꺼져있을 수도 있음)
        }
    }
}