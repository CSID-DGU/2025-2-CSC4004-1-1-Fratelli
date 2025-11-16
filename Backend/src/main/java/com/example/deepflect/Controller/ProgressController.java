package com.example.deepflect.Controller;

import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.DTO.ProgressRequest;
import com.example.deepflect.Service.ProgressManager;
import com.example.deepflect.Service.ProgressService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Controller
@RequiredArgsConstructor
@RequestMapping("/api/v1/progress")
public class ProgressController {

    @Autowired
    ProgressManager progressManager;

    @Autowired
    ProgressService progressService;

    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    @PostMapping
    public ResponseEntity<String> update(@RequestBody ProgressRequest req) {
        progressService.updateProgress(req.getTaskId(), req.getProgress());
        return ResponseEntity.ok("Progress updated");
    }

//    @GetMapping("/{taskId}")
//    public int getProgress(@PathVariable String taskId) {
//        return progressService.getProgress(taskId);
//    }

//    @GetMapping("/{taskId}")
//    public int getProgress(@PathVariable String taskId) {
//        return progressService.getProgress(taskId);
//    }

//    @PostMapping
//    public ResponseEntity<Void> receiveProgress(@RequestBody ProgressDTO dto) {
//
//        // Map, Redis 등에 저장
//        progressService.updateProgress(dto.getTaskId(), dto.getProgress());
//        System.out.println("현재 진행률: " + progressService.getProgress(dto.getTaskId()) + "%");
//        return ResponseEntity.ok().build();
//    }

    @GetMapping("/{taskId}")
    public ResponseEntity<String> getProgress(@PathVariable String taskId) {

        RestTemplate restTemplate = new RestTemplate();
        String url = "http://localhost:5000/api/v1/progress/" + taskId;

        String progress = restTemplate.getForObject(url, String.class);

        int progressPercent = progressService.getProgress(taskId);
        System.out.println("현재 진행률 = " + progressPercent + "%");

        return ResponseEntity.ok(progress);
    }

//    @GetMapping(value = "/{taskId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
//    public SseEmitter subscribe(@PathVariable String taskId) {
//
//        SseEmitter emitter = new SseEmitter(0L);
//        progressManager.addEmitter(taskId, emitter);
//
//        return emitter;
//    }

    public void pushProgress(String taskId, int value) {
        SseEmitter emitter = emitters.get(taskId);
        if (emitter != null) {
            try {
                emitter.send(SseEmitter.event().name("progress").data(value));
            } catch (Exception e) {
                emitters.remove(taskId);
            }
        }
    }

    public void pushComplete(String taskId, String downloadUrl) {
        SseEmitter emitter = emitters.get(taskId);
        if (emitter != null) {
            try {
                emitter.send(SseEmitter.event().name("complete").data(downloadUrl));
                emitter.complete();
            } catch (Exception ignored) {}
        }
        emitters.remove(taskId);
    }

}
