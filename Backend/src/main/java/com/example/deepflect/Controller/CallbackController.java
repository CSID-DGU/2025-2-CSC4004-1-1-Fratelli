package com.example.deepflect.Controller;

import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.Service.ProgressManager;
import com.example.deepflect.Service.DownloadService;
import com.example.deepflect.Service.ProgressService;
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

    @PostMapping("/ai_progress")
    public ResponseEntity<?> aiProgress(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_progress received: taskId=" + dto.getTaskId() + " progress=" + dto.getProgress());
        // update in-memory progress map for polling
        progressService.updateProgress(dto.getTaskId(), dto.getProgress());
        // push to any SSE listeners
        progressManager.updateProgress(dto.getTaskId(), dto.getProgress());
        return ResponseEntity.ok("received");
    }

    @PostMapping("/ai_finished")
    public ResponseEntity<?> aiFinished(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_finished received: taskId=" + dto.getTaskId());
        // mark complete for polling and SSE
        progressService.updateProgress(dto.getTaskId(), 100);
        progressManager.finish(dto.getTaskId());
        // save download URL for later retrieval
        if (dto.getDownloadUrl() != null && !dto.getDownloadUrl().isEmpty()) {
            downloadService.saveDownloadUrl(dto.getTaskId(), dto.getDownloadUrl());
        }
        return ResponseEntity.ok("finished");
    }
    
    @PostMapping("/ai_failed")
    public ResponseEntity<?> aiFailed(@RequestBody ProgressDTO dto) {
        System.out.println("[CallbackController] ai_failed received: taskId=" + dto.getTaskId());
        // mark as failed
        progressService.markFailed(dto.getTaskId());
        progressManager.finish(dto.getTaskId());
        return ResponseEntity.ok("failed");
    }
}
