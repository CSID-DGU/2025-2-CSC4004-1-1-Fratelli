package com.example.deepflect.DTO;

import com.example.deepflect.Entity.FileType;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class FileUploadResponse {

    private Long fileId;
    private String fileName;
    private FileType fileType;
    private LocalDateTime uploadAt;

}