package com.example.deepflect.Jwt;

import com.example.deepflect.DTO.LoginResponse;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;

import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.Date;

@Slf4j
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret-key}")
    private String secretKeyString;
    private final long ACCESS_TOKEN_EXPIRATION_MS = 1000L * 60 * 30; // 30분
    private final long REFRESH_TOKEN_EXPIRATION_MS = 1000L * 60 * 60 * 24 * 7; // 7일

    // 비밀 키 설정 메소드
    private SecretKey getSigningKey() {
        // 비밀 키 문자열을 HMAC SHA-256 키로 변환
        return Keys.hmacShaKeyFor(secretKeyString.getBytes(StandardCharsets.UTF_8));
    }

    //  JWT 토큰 생성 로직의 중복을 제거
    private String generateToken(String subject, long expirationMs) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationMs);

        return Jwts.builder()
                .setSubject(subject)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(getSigningKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    // 만료 시간을 ZonedDateTime으로 변환
    private ZonedDateTime calculateExpirationTime(long expirationMs) {
        long futureTimeMs = System.currentTimeMillis() + expirationMs;
        // 밀리초를 Instant로 변환한 후 UTC (ZoneOffset.UTC)의 ZonedDateTime으로 변환
        return Instant.ofEpochMilli(futureTimeMs).atZone(ZoneOffset.UTC);
    }

    // Access Token + Refresh Token 모두 발급
    public LoginResponse createTokenResponse(Authentication authentication) {
        // 1. 사용자 이메일(또는 ID) 추출
        String userEmail = authentication.getName();

        // 2. Access Token 생성
        String accessToken = generateToken(userEmail, ACCESS_TOKEN_EXPIRATION_MS);

        // 3. Refresh Token 생성
        String refreshToken = generateToken(userEmail, REFRESH_TOKEN_EXPIRATION_MS);

        // 4. 만료 시간 계산
        ZonedDateTime accessExpiry = calculateExpirationTime(ACCESS_TOKEN_EXPIRATION_MS);
        ZonedDateTime refreshExpiry = calculateExpirationTime(REFRESH_TOKEN_EXPIRATION_MS);

        // 5. 응답 생성
        return new LoginResponse(
                accessToken,
                refreshToken,
                accessExpiry,
                refreshExpiry
        );
    }




}
