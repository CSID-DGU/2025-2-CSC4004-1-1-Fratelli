package com.example.deepflect.DTO;

import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Files;
import com.example.deepflect.Entity.NotifyStatus;
import com.example.deepflect.Entity.Users;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class FilesDTO {
    private String taskId;
    private int progress;


}

