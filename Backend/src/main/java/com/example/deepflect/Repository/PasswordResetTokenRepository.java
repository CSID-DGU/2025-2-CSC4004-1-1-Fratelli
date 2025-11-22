package com.example.deepflect.Repository;

import com.example.deepflect.Entity.PasswordResetToken;
import com.example.deepflect.Entity.Users;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

public interface PasswordResetTokenRepository extends JpaRepository<PasswordResetToken, Long> {
    Optional<PasswordResetToken> findByToken(String token);

    void deleteByUser(Users user);
}
