package com.example.deepflect.DAO;

import com.example.deepflect.DTO.UserDTO;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.stereotype.Component;

@Component
@Transactional
public class UserDAO {

    @Autowired
    EntityManager em;

    @Autowired
    UsersRepository usersRepository;

    public void saveUser(UserDTO dto){
        usersRepository.save(UserDTO.fromDto(dto));

    }

//    // 유저 id로 유저 no 가져오기
//    public Users findByUserNum(Long userNum) {
//        String sql = "SELECT u FROM Users u WHERE u.userNum = :userNum";
//        Query query = em.createQuery(sql);
//        Users user = (Users) query.getSingleResult();
//        return user;
//    }

    public void deleteUserByNum(Long userNum) {
        Users users = em.find(Users.class, userNum);
        em.remove(users);
    }



}
