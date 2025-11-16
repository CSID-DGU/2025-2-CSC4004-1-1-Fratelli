package com.example.deepflect.Entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "Files")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class NoiseFiles {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long fileId;

    @Column(nullable = false)
    private String originalName;

    @Column(nullable = false)
    private String saveName;

    @Column(nullable = false)
    private Long size;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_num")
    private Users user;

    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();  // 업로드 시간
}
