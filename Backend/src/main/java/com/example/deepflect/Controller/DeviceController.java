package com.example.deepflect.Controller;

import com.example.deepflect.DTO.DeviceDeleteRequest;
import com.example.deepflect.DTO.DeviceRequest;
import com.example.deepflect.DTO.DeviceResponse;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.DeviceService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
public class DeviceController {

    @Autowired
    UsersRepository usersRepository;

    @Autowired
    DeviceService deviceService;
    
    // 디바이스 등록
    @PostMapping("/device")
    public ResponseEntity<DeviceResponse> registerDevice(
            @RequestBody DeviceRequest request) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UserDetails userDetails = (UserDetails) auth.getPrincipal();

        // 이메일로 Users 엔티티 조회
        Users user = usersRepository.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        DeviceResponse response = deviceService.registerDevice(user.getEmail(), request);

        if (response.isSuccess()) return ResponseEntity.ok(response);

        return ResponseEntity.badRequest().body(response);
    }
    /**
     * 디바이스 삭제
     * DELETE /api/v1/delete
     */
    @DeleteMapping("/device")
    public ResponseEntity<String> deleteDevice(@RequestBody DeviceDeleteRequest request) {
        try {
            deviceService.deleteDevice(request.getFcmToken());
            return ResponseEntity.ok("OK");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Failed to delete device");
        }
    }

}
