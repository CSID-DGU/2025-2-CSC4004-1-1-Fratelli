package com.example.deepflect.Repository;

import com.example.deepflect.Entity.Device;
import com.example.deepflect.Entity.Users;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface DeviceRepository extends JpaRepository<Device, Long> {

    Optional<Device> findByFcmToken(String fcmToken);

    List<Device> findByUser(Users user);// 중복 방지용
}
