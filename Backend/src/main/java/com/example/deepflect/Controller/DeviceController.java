package com.example.deepflect.Controller;

import com.example.deepflect.DTO.DeviceRequest;
import com.example.deepflect.DTO.DeviceResponse;
import com.example.deepflect.Service.DeviceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
public class DeviceController {

    @Autowired
    DeviceService deviceService;
    
    // 디바이스 등록
    @PostMapping("/device")
    public ResponseEntity<DeviceResponse> registerDevice(
            @RequestBody DeviceRequest request,
            @RequestParam("email") String userEmail  // 프론트에서 email 함께 전송
    ) {
        DeviceResponse response = deviceService.registerDevice(userEmail, request);

        if (response.isSuccess()) return ResponseEntity.ok(response);

        return ResponseEntity.badRequest().body(response);
    }
}
