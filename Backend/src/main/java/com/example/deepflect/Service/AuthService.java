package com.example.deepflect.Service;

import com.example.deepflect.DAO.UserDAO;
import com.example.deepflect.DTO.LoginRequest;
import com.example.deepflect.DTO.LoginResponse;
import com.example.deepflect.DTO.UserDTO;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Jwt.JwtTokenProvider;
import com.example.deepflect.Repository.JoinRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    @Autowired
    JoinRepository joinRepository;

    @Autowired
    PasswordEncoder passwordEncoder;

    @Autowired
    UserDAO userDAO;

    @Autowired
    JwtTokenProvider jwtTokenProvider;

    @Autowired
    AuthenticationManager authenticationManager;

    public void registerUser(UserDTO dto){
        // 중복 이메일(아이디) 체크
        if (joinRepository.findByEmail(dto.getEmail()).isPresent()) {
            throw new RuntimeException("이미 존재하는 이메일입니다.");
        }

        // 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(dto.getPassword());
        dto.setPassword(encodedPassword); // ✅ 암호화된 비밀번호 저장

        // DTO -> Entity 변환 후 저장
        Users user = UserDTO.fromDto(dto);
        System.out.println(user);
        joinRepository.save(user);
    }

    public LoginResponse login(LoginRequest loginRequest){
        // 1. A & B 단계: 인증 매니저를 통한 인증 실행
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        loginRequest.getEmail(), // 이메일
                        loginRequest.getPassword()  // 비밀번호
                )
        );

        return jwtTokenProvider.createTokenResponse(authentication);

    }

}
