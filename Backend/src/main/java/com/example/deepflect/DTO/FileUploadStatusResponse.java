package com.example.deepflect.DTO;

import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Status;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class FileUploadStatusResponse {
    private String taskId;
    private String fileName;
    private FileType fileType;
    private Status status; // uploading, failed, success
    private int progress; // 0-100
    private String message;
    private Timestamp timestamp; // ISO8601
}
