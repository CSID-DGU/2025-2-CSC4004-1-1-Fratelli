package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

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

    @Enumerated(EnumType.STRING)
    private UserStatus status;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    @PrePersist
    public void prePersist() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
        if (this.status == null) this.status = UserStatus.ACTIVE;
    }

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    // 양방향 매핑
    @JsonIgnore
    @OneToOne(mappedBy = "user", cascade = CascadeType.PERSIST, orphanRemoval = true, fetch = FetchType.LAZY)
    private UserTokens userTokens;

}
