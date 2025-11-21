package com.example.deepflect.Repository;

import com.example.deepflect.Entity.Users;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;


public interface UsersRepository extends CrudRepository<Users, Long> {

    Optional<Users> findByEmail(String email);

    Optional<Users> findByUserNum(@Param("userNum") Long userNum);
}
