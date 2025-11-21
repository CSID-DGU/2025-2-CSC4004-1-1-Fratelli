package com.example.deepflect.Repository;

import com.example.deepflect.Entity.Files;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FilesRepository extends JpaRepository<Files, Long> {
    Files findByTaskId(String taskId);

}
