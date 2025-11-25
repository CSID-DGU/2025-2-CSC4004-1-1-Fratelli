package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;
import java.time.Instant;
import java.time.LocalDateTime;

import static java.lang.System.currentTimeMillis;

@Entity
@Setter
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class Notification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String taskId;
    private Status status;     // success / fail
    private String fileName;
    private FileType fileType;   // video / audio
    private String message;

    private Timestamp timestamp;

    // 유저와 연결
    @ManyToOne(fetch = FetchType.LAZY)
    @JsonBackReference
    @JoinColumn(name = "user_num")
    private Users user;

    @PrePersist
    public void prePersist() {
        if (timestamp == null) {
            timestamp = Timestamp.from(Instant.now());
        }
    }

    public Notification(Users user, String message){
        this.user = user;
        this.message = message;
        this.timestamp = Timestamp.from(Instant.now()); // 현재 시각 자동 설정
    }

}
