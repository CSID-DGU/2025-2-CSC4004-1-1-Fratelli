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
public class FileUploadResponse {

    private String taskId;
    private String fileName;
    private long size; // bytes
    private FileType fileType; // "video", "image", "audio"
    private Status status; // UPLOADING, FAILED, SUCCESS
    private Timestamp timestamp; // ISO8601 timestamp string
    private String userEmail; // 업로드한 사용자 이메일

    // 기존 생성자 호환성을 위한 생성자
    public FileUploadResponse(String taskId, String fileName, long size, FileType fileType, Status status, Timestamp timestamp) {
        this.taskId = taskId;
        this.fileName = fileName;
        this.size = size;
        this.fileType = fileType;
        this.status = status;
        this.timestamp = timestamp;
    }
}