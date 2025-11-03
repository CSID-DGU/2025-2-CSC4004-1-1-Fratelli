package com.example.deepflect.Entity;

import jakarta.persistence.*;

import java.time.LocalDateTime;

@Entity
@Table(name = "Files")
public class Files {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;

    @Enumerated(EnumType.STRING)
    private MediaType mediaType;  // IMAGE or VIDEO

    private String fileName;
    private String fileUrl;
    private String thumbnailUrl;
    private Long fileSize;
    private String mimeType;
    private LocalDateTime uploadDate;
    private String description;
}
