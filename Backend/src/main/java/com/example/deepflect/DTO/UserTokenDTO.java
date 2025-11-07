package com.example.deepflect.DTO;

import com.example.deepflect.Entity.UserTokens;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class UserTokenDTO {
    private Long tokenId;

    private String accessToken;
    private String refreshToken;

    public static UserTokenDTO fromEntity(UserTokens userTokens){
        return new UserTokenDTO(
                userTokens.getTokenId(),
                userTokens.getAccessToken(),
                userTokens.getRefreshToken());
    }

    public static UserTokens fromDto(UserTokenDTO dto){
        UserTokens userTokens = new UserTokens();
        userTokens.setTokenId(dto.getTokenId());
        userTokens.setAccessToken(dto.getAccessToken());
        userTokens.setRefreshToken(dto.getRefreshToken());
        return userTokens;
    }

}
