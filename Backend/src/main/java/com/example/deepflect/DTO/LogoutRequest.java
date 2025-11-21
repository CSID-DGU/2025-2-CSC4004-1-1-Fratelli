package com.example.deepflect.DTO;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Data
public class LogoutRequest {
    private String token;
}
