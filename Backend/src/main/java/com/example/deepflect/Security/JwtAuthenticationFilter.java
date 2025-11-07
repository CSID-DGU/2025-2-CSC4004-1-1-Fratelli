package com.example.deepflect.Security;

import com.example.deepflect.Jwt.JwtTokenProvider;
import com.example.deepflect.Service.CustomUserDetailsService;
import com.example.deepflect.Service.UsersService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
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
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    JwtTokenProvider jwtTokenProvider;

    @Autowired
    CustomUserDetailsService customUserDetailsService;

//    @Override
//    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
//            throws ServletException, IOException {
//
//        String header = request.getHeader("Authorization");
//
//        if (header == null || !header.startsWith("Bearer ")) {
//            filterChain.doFilter(request, response);
//            return;
//        }
//
//        String token = header.substring(7);
//        if (!jwtTokenProvider.validateToken(token)) {
//            filterChain.doFilter(request, response);
//            return;
//        }
//
//        // ✅ 이메일 추출
//        String email = jwtTokenProvider.extractEmail(token);
//
//        // ✅ Spring Security 인증 컨텍스트에 저장
//        if (email != null && SecurityContextHolder.getContext().getAuthentication() == null) {
//            UserDetails userDetails = usersService.loadUserByUsername(email);
//
//            UsernamePasswordAuthenticationToken authentication =
//                    new UsernamePasswordAuthenticationToken(
//                            userDetails, null, userDetails.getAuthorities());
//
//            SecurityContextHolder.getContext().setAuthentication(authentication);
//        }
//
//        filterChain.doFilter(request, response);
//    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String header = request.getHeader("Authorization");

        // 헤더가 없거나 Bearer로 시작하지 않으면 필터 통과
        if (header == null || !header.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        // JWT 추출
        String token = header.substring(7);

        // 토큰 검증
        if (jwtTokenProvider.validateToken(token)) {
            String email = jwtTokenProvider.extractEmail(token);

            // 유저 정보 로드
            UserDetails userDetails = customUserDetailsService.loadUserByUsername(email);

            // 인증 객체 생성 후 SecurityContext에 저장
            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);
        }

        // 다음 필터로 진행
        filterChain.doFilter(request, response);
    }
}
