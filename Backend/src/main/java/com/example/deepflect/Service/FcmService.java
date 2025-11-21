package com.example.deepflect.Service;

import com.example.deepflect.Entity.Device;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.DeviceRepository;
import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.messaging.Message;
import com.google.firebase.messaging.Notification;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class FcmService {

    @Autowired
    DeviceRepository deviceRepository;

    public void sendNotificationToUser(Users user, String title, String body) {

        List<Device> devices = deviceRepository.findByUser(user);

        for (Device device : devices) {
            try {
                Message message = Message.builder()
                        .setToken(device.getFcmToken())
                        .setNotification(Notification.builder()
                                .setTitle(title)
                                .setBody(body)
                                .build())
                        .build();

                FirebaseMessaging.getInstance().send(message);

                System.out.println("FCM sent to: " + device.getFcmToken());

            } catch (Exception e) {
                System.out.println("❌ Failed to send FCM: " + e.getMessage());
            }
        }
    }

}
