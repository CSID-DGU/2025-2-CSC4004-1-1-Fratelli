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

import java.sql.Timestamp;
import java.time.LocalDateTime;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class FilesDTO {
    private String taskId;
    private String fileName;
    private FileType fileType;
    private long size;
    private String url;
    private String thumbnailUrl;
    private Timestamp timestamp;
//    private int progress;
}

