package com.example.deepflect.Service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
@Slf4j
public class ProgressManager {

    private final Map<String, List<SseEmitter>> emitterMap = new HashMap<>();

    public void addEmitter(String taskId, SseEmitter emitter) {
        emitterMap.computeIfAbsent(taskId, k -> new ArrayList<>()).add(emitter);
    }

    public void updateProgress(String taskId, int progress, String progressStatus) {
        List<SseEmitter> list = emitterMap.get(taskId);
        if (list == null) return;

        for (SseEmitter emitter : list) {
            try {
                emitter.send(SseEmitter.event().name("progress").data(progress));
                emitter.send(SseEmitter.event().name("progressStatus").data(progressStatus));
            } catch (IOException e) {
                emitter.complete();
            }
        }
    }

    public void finish(String taskId) {
        List<SseEmitter> list = emitterMap.get(taskId);
        if (list == null) return;

        for (SseEmitter emitter : list) {
            try {
                emitter.send(SseEmitter.event().name("finish").data("done"));
                emitter.complete();
            } catch (Exception ignored) {}
        }

        emitterMap.remove(taskId);
    }
}
