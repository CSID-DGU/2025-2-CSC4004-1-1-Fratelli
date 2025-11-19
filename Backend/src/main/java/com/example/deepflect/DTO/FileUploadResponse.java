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

}