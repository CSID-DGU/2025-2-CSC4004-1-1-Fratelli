package com.example.deepflect.DTO;

import com.example.deepflect.Entity.FileType;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
@NoArgsConstructor
public class FileUploadRequest {
    private String fileName;
    private FileType fileType;
}
