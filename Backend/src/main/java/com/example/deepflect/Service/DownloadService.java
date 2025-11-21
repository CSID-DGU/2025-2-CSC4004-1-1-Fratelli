package com.example.deepflect.Service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class DownloadService {
    
    private final Map<String, String> downloadUrlMap = new ConcurrentHashMap<>();
    private final Map<String, Long> completionTimeMap = new ConcurrentHashMap<>();

    /**
     * 작업 완료 후 다운로드 URL 저장
     */
    public void saveDownloadUrl(String taskId, String downloadUrl) {
        downloadUrlMap.put(taskId, downloadUrl);
        completionTimeMap.put(taskId, System.currentTimeMillis());
        System.out.println("[DownloadService] Saved download URL for taskId=" + taskId + ": " + downloadUrl);
    }

    /**
     * taskId로 다운로드 URL 조회
     */
    public String getDownloadUrl(String taskId) {
        return downloadUrlMap.getOrDefault(taskId, null);
    }

    /**
     * 작업 완료 여부 확인
     */
    public boolean isCompleted(String taskId) {
        return downloadUrlMap.containsKey(taskId);
    }

    /**
     * 오래된 작업 정리 (선택: 24시간 이상 지난 항목 삭제)
     */
    public void cleanupOldTasks() {
        long now = System.currentTimeMillis();
        long threshold = 24 * 60 * 60 * 1000; // 24시간
        
        downloadUrlMap.keySet().removeIf(taskId -> {
            Long completionTime = completionTimeMap.get(taskId);
            return completionTime != null && (now - completionTime) > threshold;
        });
    }
}
