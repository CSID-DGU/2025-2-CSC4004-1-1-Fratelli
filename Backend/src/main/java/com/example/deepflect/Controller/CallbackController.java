package com.example.deepflect.Controller;

import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.Service.ProgressManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;


@Controller
@RequestMapping("/api/v1/callback")
public class CallbackController {

    @Autowired
    ProgressManager progressManager;

    @PostMapping("/ai_progress")
    public void aiProgress(@RequestBody ProgressDTO dto) {
        progressManager.updateProgress(dto.getTaskId(), dto.getProgress());
    }

    @PostMapping("/ai_finished")
    public void aiFinished(@RequestBody ProgressDTO dto) {
        progressManager.finish(dto.getTaskId());
    }
}
