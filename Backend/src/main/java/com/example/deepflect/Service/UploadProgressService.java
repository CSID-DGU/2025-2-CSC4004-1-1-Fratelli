package com.example.deepflect.Service;

import com.example.deepflect.DTO.FileUploadResponse;
import com.example.deepflect.DTO.FileUploadStatusResponse;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Service
public class UploadProgressService {

    // Map taskId -> FileUploadStatusResponse
    private final ConcurrentMap<String, FileUploadStatusResponse> statusMap = new ConcurrentHashMap<>();

    // Map taskId -> FileUploadResponse (when available)
    private final ConcurrentMap<String, FileUploadResponse> uploadMap = new ConcurrentHashMap<>();

    public void saveStatus(FileUploadStatusResponse status) {
        if (status == null || status.getTaskId() == null) return;
        statusMap.put(status.getTaskId(), status);
    }

    public FileUploadStatusResponse getStatus(String taskId) {
        return statusMap.get(taskId);
    }

    public List<FileUploadStatusResponse> listStatuses() {
        return new ArrayList<>(statusMap.values());
    }

    public void saveUpload(FileUploadResponse resp) {
        if (resp == null || resp.getTaskId() == null) return;
        uploadMap.put(resp.getTaskId(), resp);
    }

    public List<FileUploadResponse> listUploads() {
        return new ArrayList<>(uploadMap.values());
    }
    
    public boolean deleteUpload(String taskId) {
        return uploadMap.remove(taskId) != null;
    }
    
    public FileUploadResponse getUpload(String taskId) {
        return uploadMap.get(taskId);
    }

}
