package com.example.deepflect.DTO;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class LogoutResponse {
    private String message;
    private Integer code;
}
