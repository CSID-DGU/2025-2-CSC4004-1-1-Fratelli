package com.example.deepflect.DTO;

import com.example.deepflect.Entity.FileType;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class ResultDownloadResponse {
    private String fileId;
    private String fileName;
    private FileType fileType;
    private long size;
    private String downloadUrl;
    private String message;
    private Timestamp timestamp;
}
