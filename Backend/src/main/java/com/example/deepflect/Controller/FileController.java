package com.example.deepflect.Controller;

import com.example.deepflect.DTO.FileUploadRequest;
import com.example.deepflect.DTO.FileUploadResponse;
import com.example.deepflect.DTO.FilesDTO;
import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.Entity.Files;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.AiService;
import com.example.deepflect.Service.ProgressService;
import org.springframework.core.io.Resource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import com.example.deepflect.Service.FileService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/files")
public class FileController {

    @Autowired
    UsersRepository usersRepository;

    @Autowired
    FileService fileService;

    @Autowired
    AiService aiService;

    @Autowired
    ProgressService progressService;

    @Value("${file.dir}")
    private String fileDir;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<String> upload(@RequestParam("file") MultipartFile file) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UserDetails userDetails = (UserDetails) auth.getPrincipal();

        // 이메일로 Users 엔티티 조회
        Users user = usersRepository.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        // 업로드 폴더 생성 (uploadedFiles/user_email)
        String userFolderPath = fileDir + "/" + user.getEmail(); // fileDir = /Users/betty/OSS_team1/uploadedFiles
        File folder = new File(userFolderPath);
        if (!folder.exists()) {
            folder.mkdirs(); // 상위 폴더까지 생성
        }

        String taskId = UUID.randomUUID().toString();
        String savedPath = fileService.saveOriginalFile(file, user, taskId);
        aiService.requestNoiseProcessing(taskId, savedPath);

        return ResponseEntity.ok(taskId);
    }

    @GetMapping("/download/{taskId}/{fileName}")
    public ResponseEntity<Resource> download(@PathVariable String taskId, @PathVariable String fileName) {
        File file = new File(fileDir + "/" + taskId + "_" + fileName);
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }

        Resource resource = new FileSystemResource(file);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getName() + "\"")
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .body(resource);
    }


}
