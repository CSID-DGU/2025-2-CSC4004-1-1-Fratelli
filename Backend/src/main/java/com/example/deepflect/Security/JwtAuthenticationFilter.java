package com.example.deepflect.Security;

import com.example.deepflect.Jwt.JwtTokenProvider;
import com.example.deepflect.Service.CustomUserDetailsService;
import com.example.deepflect.Service.UsersService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
@RequiredArgsConstructor
@Slf4j
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    JwtTokenProvider jwtTokenProvider;

    @Autowired
    CustomUserDetailsService customUserDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String requestUri = request.getRequestURI();
        String queryString = request.getQueryString(); // token= 값 포함 여부 확인
        
        // 콜백 엔드포인트 및 공개 다운로드 엔드포인트는 JWT 검증 스킵
        if (requestUri.startsWith("/api/v1/auth/register/") || requestUri.startsWith("/api/v1/auth/login/") ||
                requestUri.startsWith("/api/v1/auth/refresh/") || requestUri.startsWith("/api/v1/callback/") ||
                requestUri.startsWith("/api/v1/files/download-protected/") ||
                (requestUri.startsWith("/api/v1/auth/password-reset")&& queryString != null && queryString.startsWith("token="))) {
            filterChain.doFilter(request, response);
            return;
        }

        System.out.println("JWT 필터 동작 시작: " + requestUri);
        System.out.println("Authorization 헤더: " + request.getHeader("Authorization"));
        String header = request.getHeader("Authorization");
        System.out.println(header);

        if (header == null || !header.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = header.substring(7);

        try {
            if (jwtTokenProvider.validateToken(token)) {
                String email = jwtTokenProvider.extractEmail(token);
                log.info(email);
                UserDetails userDetails = customUserDetailsService.loadUserByUsername(email);
                log.info("=========================================");
                log.info(userDetails.getUsername());
                log.info("=========================================");
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
                SecurityContextHolder.getContext().setAuthentication(authentication);

                // ✅ 로그인 상태 확인 로그
                System.out.println("로그인 됨: " + userDetails.getUsername());

            } else {
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.getWriter().write("Invalid or expired JWT token");
                return;
            }
        } catch (Exception e) {
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.getWriter().write("JWT processing error");
            return;
        }

        filterChain.doFilter(request, response);
    }

}
