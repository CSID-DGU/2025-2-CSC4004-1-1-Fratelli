package com.example.deepflect.Jwt;

import com.example.deepflect.DTO.LoginResponse;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
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

    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(secretKeyString.getBytes(StandardCharsets.UTF_8));
    }

    private String generateToken(String subject, long expirationMs) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationMs);

        log.debug("[JWT 생성] subject={}, now={}, exp={}", subject, now, expiryDate);

        return Jwts.builder()
                .setSubject(subject)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                // 필요 시 roles 등 claims 추가
                //.claim("roles", roles)
                .signWith(getSigningKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    public LoginResponse createTokenResponse(Authentication authentication) {
        String userEmail = authentication.getName();

        System.out.println("=======================================");
        System.out.println(userEmail);
        System.out.println("=======================================");

        String accessToken = generateToken(userEmail, ACCESS_TOKEN_EXPIRATION_MS);
        String refreshToken = generateToken(userEmail, REFRESH_TOKEN_EXPIRATION_MS);

        ZonedDateTime accessExpiry = Instant.ofEpochMilli(System.currentTimeMillis() + ACCESS_TOKEN_EXPIRATION_MS).atZone(ZoneOffset.UTC);
        ZonedDateTime refreshExpiry = Instant.ofEpochMilli(System.currentTimeMillis() + REFRESH_TOKEN_EXPIRATION_MS).atZone(ZoneOffset.UTC);

        return new LoginResponse(accessToken, refreshToken, accessExpiry, refreshExpiry);
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .setAllowedClockSkewSeconds(60) // 1분 유예
                    .build()
                    .parseClaimsJws(token);

            return true;
        } catch (ExpiredJwtException e) {
            log.error("Token expired at: {}", e.getClaims().getExpiration());
            log.error("Server time: {}", new Date());
            return false;
        } catch (JwtException | SecurityException e) {
            log.error("Invalid token: {}", e.getMessage());
            return false;
        }
    }

    public String extractEmail(String token) {
        try {
            return Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .build()
                    .parseClaimsJws(token)
                    .getBody()
                    .getSubject();
        } catch (JwtException e) {
            log.error("토큰에서 이메일 추출 실패: {}", e.getMessage());
            return null;
        }
    }


}
