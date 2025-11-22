package com.example.deepflect.Service;

import com.example.deepflect.Entity.PasswordResetToken;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.PasswordResetTokenRepository;
import com.example.deepflect.Repository.UsersRepository;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
@Transactional
public class PasswordResetService {

    @Autowired
    UsersRepository usersRepository;

    @Autowired
    PasswordResetTokenRepository passwordResetTokenRepository;

    @Autowired
    JavaMailSender mailSender;

    @Autowired
    PasswordEncoder passwordEncoder;

    @Autowired
    QueryService queryService;

    public void sendPasswordResetMail(String email) {
        Users user = usersRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("해당 이메일이 존재하지 않습니다."));


        // 기존 토큰 존재하면 삭제
        queryService.deleteByUserNum(user.getUserNum());

        String token = UUID.randomUUID().toString();

        PasswordResetToken resetToken = new PasswordResetToken();
        resetToken.setToken(token);
        resetToken.setUser(user);
        resetToken.setExpiryDate(LocalDateTime.now().plusMinutes(30));

        passwordResetTokenRepository.save(resetToken);

        String link = "http://localhost:8080/api/v1/auth/reset-password?token=" + token;

        SimpleMailMessage message = new SimpleMailMessage();
        message.setTo(email);
        message.setSubject("비밀번호 재설정 안내");
        message.setText("비밀번호 재설정 링크: " + link);

        mailSender.send(message);
    }

    public void resetPassword(String token, String newPassword) {
        PasswordResetToken resetToken = passwordResetTokenRepository.findByToken(token)
                .orElseThrow(() -> new RuntimeException("유효하지 않은 토큰입니다."));

        if (resetToken.isExpired()) {
            throw new RuntimeException("토큰이 만료되었습니다.");
        }

        Users user = resetToken.getUser();
        user.setPassword(passwordEncoder.encode(newPassword));
        usersRepository.save(user);

        passwordResetTokenRepository.delete(resetToken); // 사용 후 토큰 삭제
    }
}
