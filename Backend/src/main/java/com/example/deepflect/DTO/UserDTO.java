package com.example.deepflect.DTO;

import com.example.deepflect.Entity.UserStatus;
import com.example.deepflect.Entity.Users;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class UserDTO {

//    private long userNum;
    private String email;
    private String password;
    private String userName;
    private UserStatus status;


    public static UserDTO fromEntity(Users users){
        return new UserDTO(
                users.getPassword(),
                users.getEmail(),
                users.getUserName(),
                users.getStatus());
    }

    public static Users fromDto(UserDTO dto){
        Users users = new Users();
        users.setEmail(dto.getEmail());
        users.setPassword(dto.getPassword());
        users.setUserName(dto.getUserName());
        users.setStatus(dto.getStatus());
        return users;
    }

}
