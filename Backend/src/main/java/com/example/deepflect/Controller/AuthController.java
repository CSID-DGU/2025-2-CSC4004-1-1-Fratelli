package com.example.deepflect.Controller;

import com.example.deepflect.DTO.*;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.AuthService;
import com.example.deepflect.Service.QueryService;
import com.example.deepflect.Service.UsersService;
import jakarta.validation.Valid;
import org.hibernate.sql.Update;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

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
            Users user = getNewUserInfo(updateUserRequest, userOptional);
            System.out.println("-------------------------" + user.toString());
            queryService.saveModifyUserInfo(user.getUserNum(), user.getUserName(), user.getPassword());
//            usersRepository.save(user); // DB 반영
            return ResponseEntity.ok(user);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
    }

    private static Users getNewUserInfo(UpdateUserRequest updateUserRequest, Optional<Users> userOptional) {
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
        if (updateUserRequest.getPassword() != null) user.setPassword(updateUserRequest.getPassword());
        // 다른 업데이트 필드 필요 시 추가
        if (updateUserRequest.getUserName() != null) user.setUserName(updateUserRequest.getUserName());
        return user;
    }


    @DeleteMapping("/delete/{userNum}")
    public ResponseEntity<String> deleteUser(@PathVariable("userNum") Long userNum) {
        boolean deleted = usersService.deleteUserByNum(userNum);

        if (deleted) {
            return ResponseEntity.ok("{\"message\": \"User deleted successfully\"}");
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body("{\"message\": \"User not found\"}");
        }
    }

}
