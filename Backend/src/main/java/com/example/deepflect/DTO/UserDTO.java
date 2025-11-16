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


    public static UserDTO fromEntity(Users users){
        return new UserDTO(
                users.getPassword(),
                users.getEmail(),
                users.getUserName());
    }

    public static Users fromDto(UserDTO dto){
        Users users = new Users();
        users.setEmail(dto.getEmail());
        users.setPassword(dto.getPassword());
        users.setUserName(dto.getUserName());
        return users;
    }

}
