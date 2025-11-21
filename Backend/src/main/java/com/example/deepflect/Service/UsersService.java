package com.example.deepflect.Service;

import com.example.deepflect.DAO.UserDAO;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Optional;

@Service
@Transactional
public class UsersService implements UserDetailsService {


    @Autowired
    private UsersRepository usersRepository;

    @Autowired
    private UserDAO userDAO;

    @Autowired
    private QueryService queryService;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        Users user = usersRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("해당 이메일의 사용자를 찾을 수 없습니다: " + email));

        // Spring Security의 User 객체 반환 (email + 암호화된 비밀번호)
        return new User(
                user.getEmail(),
                user.getPassword(),
                Collections.emptyList()
        );
    }

    public boolean deleteUserByNum(Long userNum) {
        Optional<Users> user = queryService.findByUserNum(userNum); // 존재하는 사용자 조회
        if (user != null) {
            userDAO.deleteUserByNum(userNum); // 존재하면 삭제
            return true; // 삭제 성공
        } else {
            return false; // 삭제 실패, 사용자 없음
        }
    }
}

