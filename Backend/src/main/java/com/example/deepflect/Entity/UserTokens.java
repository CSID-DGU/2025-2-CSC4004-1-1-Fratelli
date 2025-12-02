package com.example.deepflect.Entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;


@Entity
@Table(name = "user_tokens")
@Getter
@Setter
@ToString(exclude = "user")  // 이 줄 추가
@NoArgsConstructor
@AllArgsConstructor
public class UserTokens {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long tokenId;

    private String accessToken;
    private String refreshToken;

    // 외래키: Users.id
    @JsonIgnore
    @OneToOne
    @JoinColumn(name = "user_num", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    private Users user;

}
