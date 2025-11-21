package com.example.deepflect.Service;

import com.example.deepflect.DTO.DeviceRequest;
import com.example.deepflect.DTO.DeviceResponse;
import com.example.deepflect.Entity.Device;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.DeviceRepository;
import com.example.deepflect.Repository.UsersRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class DeviceService {

    @Autowired
    DeviceRepository deviceRepository;

    @Autowired
    UsersRepository usersRepository;

    public DeviceResponse registerDevice(String userEmail, DeviceRequest request) {

        // 1. 사용자 확인
        Users user = usersRepository.findByEmail(userEmail)
                .orElse(null);

        if (user == null) {
            return new DeviceResponse(false, "User not found");
        }

        // 2. 이미 동일한 토큰이 있다면 무시
        Optional<Device> existing = deviceRepository.findByFcmToken(request.getFcmToken());

        if (existing.isPresent()) {
            return new DeviceResponse(true, "Already registered");
        }

        // 3. 새 디바이스 저장
        Device device = Device.builder()
                .fcmToken(request.getFcmToken())
                .user(user)
                .build();

        deviceRepository.save(device);

        return new DeviceResponse(true, "Device register successfully");
    }
}
