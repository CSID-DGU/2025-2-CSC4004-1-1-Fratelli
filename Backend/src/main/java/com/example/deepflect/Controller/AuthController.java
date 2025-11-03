package com.example.deepflect.Controller;

import com.example.deepflect.DTO.LoginResponse;
import com.example.deepflect.DTO.LoginRequest;
import com.example.deepflect.DTO.UserDTO;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Service.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    AuthService authService;


    @PostMapping("/register")
    public ResponseEntity<String> register(@RequestBody UserDTO dto) {
        authService.registerUser(dto);
        return ResponseEntity.ok("회원가입이 완료되었습니다.");
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest loginRequest){
//        Users users = UserDTO.fromDto(dto);
//        authService.loginUser(dto);
        LoginResponse loginResponse = authService.login(loginRequest);
        return ResponseEntity.ok(loginResponse);
    }


}
