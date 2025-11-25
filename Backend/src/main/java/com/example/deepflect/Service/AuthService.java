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

import java.time.LocalDateTime;
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

    // 토큰 저장 및 유저 상태 업데이트
    private void saveTokenForUser(Users user, LoginResponse tokens) {
        // 기존 토큰이 있으면 삭제
        if (user.getUserTokens() != null) {
            queryService.deleteToken(user.getUserTokens().getTokenId());
        }

        // 새 토큰 엔티티 생성
        UserTokens userTokens = new UserTokens();
        userTokens.setUser(user);
        userTokens.setAccessToken(tokens.getAccessToken());
        userTokens.setRefreshToken(tokens.getRefreshToken());

        // 유저 상태 업데이트 및 DB 반영
        usersRepository.save(user);  // 반드시 저장해야 DB에 반영됨

        // 토큰 저장
        userTokenRepository.save(userTokens);

        log.info("AccessToken/RefreshToken stored for {}", user.getEmail());
    }

    // 로그인 시 토큰 발급 및 저장
    public LoginResponse login(LoginRequest loginRequest) {
        log.info("Login attempt for email={}", loginRequest.getEmail());

        // 유저 조회
        Users user = usersRepository.findByEmail(loginRequest.getEmail())
                .orElseThrow(() -> new RuntimeException("존재하지 않는 이메일입니다."));

        // 인증 시도
        Authentication authentication;
        try {
            authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(
                            loginRequest.getEmail(),
                            loginRequest.getPassword()
                    )
            );
        } catch (Exception e) {
            log.error("Authenticate exception for {}: {}", loginRequest.getEmail(), e.toString(), e);
            throw e;
        }

        // JWT 토큰 생성
        LoginResponse tokens = jwtTokenProvider.createTokenResponse(authentication);

        // DB에 토큰 저장 + 유저 상태 ACTIVE 반영
        saveTokenForUser(user, tokens);

        return tokens;
    }

    public LoginResponse reissue(String refreshToken) {

        // 1. RefreshToken 유효성 검사 (서명/만료)
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            throw new RuntimeException("Refresh Token is invalid or expired");
        }

        // 2. Refresh Token에서 사용자 이메일 가져오기
        String userEmail = jwtTokenProvider.extractEmail(refreshToken);

        // 3. DB에서 저장된 Refresh Token 불러오기
        Users user = usersRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("User not found"));

        UserTokens userTokens = user.getUserTokens();

        if (userTokens == null) {
            throw new RuntimeException("User has no refresh token in DB");
        }

        // 4. DB의 RefreshToken과 일치하는지 확인
        if (!userTokens.getRefreshToken().equals(refreshToken)) {
            throw new RuntimeException("Refresh token does not match stored token");
        }

        // 5. 새 토큰 발급
        Authentication authentication =
                new UsernamePasswordAuthenticationToken(userEmail, null, List.of());

        LoginResponse newTokens = jwtTokenProvider.createTokenResponse(authentication);

        // 6. DB에 새 Refresh Token 업데이트
        userTokens.setRefreshToken(newTokens.getRefreshToken());
        userTokens.setAccessToken(newTokens.getAccessToken());

        userTokenRepository.save(userTokens);

        return newTokens;
    }

    public boolean deleteByEmail(String email) {
//        Optional<UserTokens> userToken = userTokenRepository.findByAccessToken(token);
//        System.out.println("=====================================================");
//        System.out.println(userToken.get().getTokenId());
//        System.out.println("=====================================================");

        // DB에서 토큰 조회
        Optional<UserTokens> userTokenOpt = userTokenRepository.findByUser_Email(email);

        if (userTokenOpt.isPresent()) {
            UserTokens userToken = userTokenOpt.get();
            Users user = userToken.getUser();

            Long tokenId = userToken.getTokenId();
            // 사용자 상태 변경 (선택)

            // 토큰 삭제
            queryService.deleteToken(tokenId);

            log.info("로그아웃 완료: {}", user.getEmail());
            return true;
        } else {
            log.warn("DB에서 이메일을 찾을 수 없음: {}", email);
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

    public Users getNewUserInfo(UpdateUserRequest updateUserRequest, Optional<Users> userOptional) {
        Users user = userOptional.get();

        // 원하는 필드만 업데이트
//            if (updateUserRequest.getEmail() != null && !updateUserRequest.getEmail().isEmpty()) {
//                Optional<Users> existingUser = usersRepository.findByEmail(updateUserRequest.getEmail());
//                if (existingUser.isPresent() && !existingUser.get().getUserNum().equals(user.getUserNum())) {
//                    // 다른 계정이 이미 사용 중인 이메일
//                    return ResponseEntity.status(HttpStatus.CONFLICT)
//                            .body(null); // 혹은 에러 메시지 DTO 반환
//                }
//                user.setEmail(updateUserRequest.getEmail());
//            }
        if (updateUserRequest.getPassword() != null) {
            user.setPassword(updateUserRequest.getPassword());
            user.setUpdatedAt(LocalDateTime.now());
        }
        // 다른 업데이트 필드 필요 시 추가
        if (updateUserRequest.getUserName() != null) {
            user.setUserName(updateUserRequest.getUserName());
            user.setUpdatedAt(LocalDateTime.now());
        }
        return user;

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
