package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Getter
@Setter
@Table(name="users")
@ToString(exclude = "userTokens")
@NoArgsConstructor
@AllArgsConstructor
public class Users{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long userNum;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(length = 100)
    private String password;

    @Column(name = "user_name", length = 100)
    private String userName;

    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime updatedAt;

    // 양방향 매핑
    @JsonIgnore
    @OneToOne(mappedBy = "user", cascade = CascadeType.PERSIST, orphanRemoval = true, fetch = FetchType.LAZY)
    private UserTokens userTokens;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    @JsonManagedReference
    private List<Files> filesList = new ArrayList<>();

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    @JsonManagedReference
    private List<Device> devices = new ArrayList<>();

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    @JsonManagedReference
    private List<Notification> Notifications = new ArrayList<>();

    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private PasswordResetToken passwordResetToken;
}
