package com.example.deepflect.Service;

import com.example.deepflect.DAO.UserDAO;
import com.example.deepflect.Entity.Users;
import jakarta.persistence.EntityManager;
import jakarta.persistence.NoResultException;
import jakarta.persistence.Query;
import jakarta.persistence.TypedQuery;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@Transactional
public class QueryService {

    @Autowired
    PasswordEncoder passwordEncoder;

    @Autowired
    EntityManager em;

//    public UserToken findToken(Long tokenId){
//        String sql = "SELECT u FROM Users u WHERE u."
//    }

    public void deleteToken(Long tokenId){
        String sql = "DELETE FROM UserTokens u WHERE u.tokenId = :tokenId";
        em.createQuery(sql)
                .setParameter("tokenId", tokenId)
                .executeUpdate();  // DELETE는 executeUpdate() 사용
    }

    public Optional<Users> findByUserNum(Long userNum){
        String sql = "SELECT u FROM Users u WHERE u.userNum = :userNum";
        TypedQuery<Users> query = em.createQuery(sql, Users.class)
                .setParameter("userNum", userNum);
        return Optional.ofNullable(query.getSingleResult());
    }

    public void saveModifyUserInfo(Long userNum, String newUserName, String newPassword) {
        StringBuilder sql = new StringBuilder("UPDATE Users u SET ");
        boolean needComma = false;

        if (newUserName != null && !newUserName.isEmpty()) {
            sql.append("u.userName = :newUserName");
            needComma = true;
        }
        if (newPassword != null && !newPassword.isEmpty()) {
            if (needComma) sql.append(", ");
            sql.append("u.password = :newPassword");
            needComma = true;
        }

        // 항상 updatedAt은 갱신
        if (needComma) sql.append(", ");
        sql.append("u.updatedAt = CURRENT_TIMESTAMP WHERE u.userNum = :userNum");

        var query = em.createQuery(sql.toString());
        query.setParameter("userNum", userNum);

        if (newUserName != null && !newUserName.isEmpty()) {
            query.setParameter("newUserName", newUserName);
        }
        if (newPassword != null && !newPassword.isEmpty()) {
            String encodedPassword = passwordEncoder.encode(newPassword);
            query.setParameter("newPassword", encodedPassword);
        }

        query.executeUpdate();
    }


    public void deleteByUserNum(Long userNum){
        String sql = "DELETE FROM PasswordResetToken u WHERE u.user.userNum = :userNum";
        em.createQuery(sql)
                .setParameter("userNum", userNum)
                .executeUpdate();  // DELETE는 executeUpdate() 사용
    }

//    public boolean deleteUserById(Long userNum) {
//        Users user = em.find(Users.class, userNum);
//        if (user != null) {
//            em.remove(user);
//            return true;
//        }
//        return false;
//    }

}
