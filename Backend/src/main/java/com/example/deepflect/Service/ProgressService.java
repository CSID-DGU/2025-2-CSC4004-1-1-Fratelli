package com.example.deepflect.Service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ProgressService {

    private final Map<String, Integer> progressMap = new ConcurrentHashMap<>();
    private final Map<String, Boolean> failedMap = new ConcurrentHashMap<>();

    public void updateProgress(String taskId, int progress) {
        progressMap.put(taskId, progress);
    }

    public int getProgress(String taskId) {
        return progressMap.getOrDefault(taskId, 0);
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
