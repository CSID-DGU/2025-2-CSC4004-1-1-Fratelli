package com.example.deepflect.Repository;

import com.example.deepflect.Entity.UserTokens;
//import com.example.deepflect.Entity.Users;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserTokenRepository extends JpaRepository<UserTokens, Long> {
    Optional<UserTokens> findByAccessToken(String accessToken);
    void deleteByTokenId(Long tokenId);
    Optional<UserTokens> findByUser_Email(String email);
}
