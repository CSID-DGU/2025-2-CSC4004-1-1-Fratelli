package com.example.deepflect.DAO;

import com.example.deepflect.DTO.UserDTO;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.JoinRepository;
import jakarta.persistence.EntityManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class UserDAO {

    @Autowired
    EntityManager em;

    @Autowired
    JoinRepository joinRepository;

    public void saveUser(UserDTO dto){
        joinRepository.save(UserDTO.fromDto(dto));

    }


}
