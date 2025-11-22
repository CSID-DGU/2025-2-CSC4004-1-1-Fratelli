package com.example.deepflect.Controller;

import com.example.deepflect.DTO.*;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.AuthService;
import com.example.deepflect.Service.PasswordResetService;
import com.example.deepflect.Service.QueryService;
import com.example.deepflect.Service.UsersService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    AuthService authService;

    @Autowired
    QueryService queryService;

    @Autowired
    UsersService usersService;

    @Autowired
    PasswordResetService passwordResetService;

    @Autowired
    UsersRepository usersRepository;

    @PostMapping("/register")
    public ResponseEntity<String> register(@RequestBody UserDTO dto) {
        authService.registerUser(dto);
        return ResponseEntity.ok("회원가입이 완료되었습니다.");
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest loginRequest){
//        Users users = UserDTO.fromDto(dto);
//        authService.loginUser(dto);
        authService.cleanExpiredTokens();
        LoginResponse loginResponse = authService.login(loginRequest);
        return ResponseEntity.ok(loginResponse);
    }

    @GetMapping("/check-login")
    public ResponseEntity<String> checkLogin() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();

        if (auth != null && auth.isAuthenticated() &&
                !(auth.getPrincipal() instanceof String && auth.getPrincipal().equals("anonymousUser"))) {

            UserDetails userDetails = (UserDetails) auth.getPrincipal();
            return ResponseEntity.ok("로그인됨: " + userDetails.getUsername());
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("로그인 필요");
        }
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(@RequestHeader("Authorization") String refreshToken) {

        if (refreshToken == null || !refreshToken.startsWith("Bearer ")) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("Refresh token required");
        }

        String token = refreshToken.substring(7);

        LoginResponse newTokens = authService.reissue(token);

        return ResponseEntity.ok(newTokens);
    }

    @PostMapping("/logout")
    public ResponseEntity<LogoutResponse> logout(@RequestBody LogoutRequest logoutRequest) {
        String token = logoutRequest.getToken();

        boolean isDeleted = authService.deleteToken(token);

        if (isDeleted) {
            return ResponseEntity.ok(new LogoutResponse("Logout success", 200));
        } else {
            return ResponseEntity.status(401).body(new LogoutResponse("Invalid token", 401));
        }
    }

    @GetMapping("/user/{userNum}")
    public ResponseEntity<Users> getUserByNum(@PathVariable("userNum") Long userNum) {
        Optional<Users> userOptional = queryService.findByUserNum(userNum);

        if (userOptional.isPresent()) {
            return ResponseEntity.ok(userOptional.get());
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
    }

    @PatchMapping("/user")
    public ResponseEntity<Users> updateByUserNum(@RequestBody UpdateUserRequest updateUserRequest) {
//        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
//
//        if (authentication == null || !authentication.isAuthenticated()) {
//            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
//        }

        String email = updateUserRequest.getEmail(); // email로 JWT 인증
        System.out.println("-------------------------------------------------");
        System.out.println(email);
        System.out.println("-------------------------------------------------");

        Optional<Users> userOptional = usersRepository.findByEmail(email);

        if (userOptional.isPresent()) {
            Users user = authService.getNewUserInfo(updateUserRequest, userOptional);
            System.out.println("-------------------------" + user.toString());
            queryService.saveModifyUserInfo(user.getUserNum(), user.getUserName(), user.getPassword());
//            usersRepository.save(user); // DB 반영
            return ResponseEntity.ok(user);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
    }

    @PostMapping("/password-reset")
    public ResponseEntity<String> passwordReset(@RequestBody PasswordResetRequest request) {
        passwordResetService.sendPasswordResetMail(request.getEmail());
        return ResponseEntity.ok("비밀번호 재설정 이메일이 발송되었습니다.");
    }


    @DeleteMapping("/quit")
    public ResponseEntity<?> deleteUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UserDetails userDetails = (UserDetails) auth.getPrincipal();

        // 이메일로 Users 엔티티 조회
        Users user = usersRepository.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        boolean deleted = usersService.deleteUserByNum(user.getUserNum());

        if (deleted) return ResponseEntity.ok(Map.of("message", "User deleted successfully"));
        else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("message", "User not found"));
        }

//        if (deleted) {
//            return ResponseEntity.ok("{\"message\": \"User deleted successfully\"}");
//        } else {
//            return ResponseEntity.status(HttpStatus.NOT_FOUND)
//                    .body("{\"message\": \"User not found\"}");
//        }
    }

}
