package com.example.deepflect.Service;

import com.example.deepflect.DAO.UserDAO;
import com.example.deepflect.DTO.*;
import com.example.deepflect.Entity.UserStatus;
import com.example.deepflect.Entity.UserTokens;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Jwt.JwtTokenProvider;
import com.example.deepflect.Repository.UsersRepository;

import com.example.deepflect.Repository.UserTokenRepository;
import jakarta.transaction.Transactional;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;


import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@Transactional
public class AuthService {

    @Autowired
    UsersRepository usersRepository;

    @Autowired
    UserTokenRepository userTokenRepository;

    @Autowired
    QueryService queryService;

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
        if (usersRepository.findByEmail(dto.getEmail()).isPresent()) {
            throw new RuntimeException("이미 존재하는 이메일입니다.");
        }

        // 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(dto.getPassword());
        dto.setPassword(encodedPassword); // ✅ 암호화된 비밀번호 저장

        // DTO -> Entity 변환 후 저장
        Users user = UserDTO.fromDto(dto);
        System.out.println(user);
        usersRepository.save(user);
    }

//    public LoginResponse login(LoginRequest loginRequest){
//        // 1. A & B 단계: 인증 매니저를 통한 인증 실행
//        Authentication authentication = authenticationManager.authenticate(
//                new UsernamePasswordAuthenticationToken(
//                        loginRequest.getEmail(), // 이메일
//                        loginRequest.getPassword()  // 비밀번호
//                )
//        );
//
//        return jwtTokenProvider.createTokenResponse(authentication);
//    }

    private void saveTokenForUser(Users user, LoginResponse tokens) {
        // 기존 토큰이 있으면 삭제
        if (user.getUserTokens() != null) {
            userTokenRepository.delete(user.getUserTokens());
        }

        // 새 토큰 엔티티 생성
        UserTokens userTokens = new UserTokens();
        userTokens.setUser(user);
        userTokens.setAccessToken(tokens.getAccessToken());
        userTokens.setRefreshToken(tokens.getRefreshToken());

        // 유저 상태 업데이트 (선택)
        user.setStatus(UserStatus.ACTIVE);

        // 저장
        userTokenRepository.save(userTokens);

        log.info("AccessToken/RefreshToken stored for {}", user.getEmail());
    }

    // 로그인 시 토큰 저장
    public LoginResponse login(LoginRequest loginRequest) {
        log.info("Login attempt for email={}", loginRequest.getEmail());

        // (선택) DB에 존재 여부 빠르게 검사 — 자세한 비밀번호 비교는 authenticationManager 에 맡김
        Users user = usersRepository.findByEmail(loginRequest.getEmail())
                .orElseThrow(() -> new RuntimeException("존재하지 않는 이메일입니다."));

        Authentication authentication;
        try {
            authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            loginRequest.getEmail(),
                            loginRequest.getPassword()
                    )
            );
        } catch (Exception e) {
            // Exception 내부에서 StackOverflow가 발생하면 이 라인까지 도달 못함(그럼 바로 JVM 오류)
            log.error("Authenticate exception for {}: {}", loginRequest.getEmail(), e.toString(), e);
            throw e;
        }

        // authentication이 성공하면 jwt 발급
        LoginResponse tokens = jwtTokenProvider.createTokenResponse(authentication);

        // 토큰 저장 로직은 별도 메서드로 분리해도 좋음
        saveTokenForUser(user, tokens);

        return tokens;
    }


    public boolean deleteToken(String accessToken) {
//        Optional<UserTokens> userToken = userTokenRepository.findByAccessToken(token);
//        System.out.println("=====================================================");
//        System.out.println(userToken.get().getTokenId());
//        System.out.println("=====================================================");

        // DB에서 토큰 조회
        Optional<UserTokens> userTokenOpt = userTokenRepository.findByAccessToken(accessToken);

        if (userTokenOpt.isPresent()) {
            UserTokens userToken = userTokenOpt.get();
            Users user = userToken.getUser();

            Long tokenId = userToken.getTokenId();
            // 사용자 상태 변경 (선택)
            user.setStatus(UserStatus.INACTIVE);

            // 토큰 삭제
            queryService.deleteToken(tokenId);

            log.info("로그아웃 완료: {}", user.getEmail());
            return true;
        } else {
            log.warn("DB에서 토큰을 찾을 수 없음: {}", accessToken);
            return false;
        }
    }

    // ✅ 만료된 토큰 정리 (로그인 시마다 실행)
    public void cleanExpiredTokens() {
        List<UserTokens> tokens = userTokenRepository.findAll();
        for (UserTokens token : tokens) {
            if (!jwtTokenProvider.validateToken(token.getAccessToken())) {
                userTokenRepository.delete(token);
            }
        }
    }

//    public boolean deleteToken(String email) {
//        Optional<UserToken> userToken = userTokenRepository.findByEmail(email);
////        System.out.println(userToken);
//        Long tokenId = userToken.get().getTokenId();
//        System.out.println("--------------------------------------------------------------");
//        System.out.println(userToken);
//        System.out.println("--------------------------------------------------------------");
//        if (userToken.get().getUser().getStatus() == ACTIVE) {
//            userTokenRepository.deleteByTokenId(tokenId);
//            return true; // ✅ 로그아웃 성공
//        } else {
//            return false; // ❌ 유효하지 않은 토큰
//        }
//    }

//    // 토큰 유효성 확인
//    public boolean isTokenValid(String token) {
//        return userTokenRepository.findByAccessToken(token).isPresent();
//    }

}
