package com.example.deepflect.Service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ProgressService {

    private final Map<String, Integer> progressMap = new ConcurrentHashMap<>();
    private final Map<String, String> progressStatusMap = new ConcurrentHashMap<>();
    private final Map<String, Boolean> failedMap = new ConcurrentHashMap<>();

//    public void updateProgress(String taskId, int progress, String progressStatus) {
//        progressMap.put(taskId, progress);
//        progressStatusMap.put(taskId, progressStatus);
//    }

    public void updateProgress(String taskId, int progress, String progressStatus) {
        if (taskId == null) {
            throw new IllegalArgumentException("taskId cannot be null");
        }

        // progressStatus는 null일 수 있으므로 기본값 넣기
        if (progressStatus == null) {
            progressStatus = "UNKNOWN"; // 또는 "PENDING", "DONE" 등 적합한 상태
        }

        progressMap.put(taskId, progress);
        progressStatusMap.put(taskId, progressStatus);
    }

    public int getProgress(String taskId) {
        return progressMap.getOrDefault(taskId, 0);
    }

    public String getProgressStatus(String taskId) {
        return progressStatusMap.getOrDefault(taskId, "start");
    }

    public boolean isDone(String taskId) {
        return progressMap.getOrDefault(taskId, 0) >= 100;
    }
    
    public void markFailed(String taskId) {
        failedMap.put(taskId, true);
    }
    
    public boolean isFailed(String taskId) {
        return failedMap.getOrDefault(taskId, false);
    }
}
