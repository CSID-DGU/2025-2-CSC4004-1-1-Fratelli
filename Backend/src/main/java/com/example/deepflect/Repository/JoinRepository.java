package com.example.deepflect.Repository;

import com.example.deepflect.Entity.Users;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

//@Repository
public interface JoinRepository extends CrudRepository<Users, Long> {

    Optional<Users> findByEmail(String email);

}
