package com.example.deepflect.Service;

import com.example.deepflect.Entity.Files;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.FilesRepository;
import com.example.deepflect.Repository.UsersRepository;
import jakarta.transaction.Transactional;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.userdetails.User;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;

@Service
@Transactional
@Slf4j
public class FileService {

    @Value("${file.dir}")
    private String fileDir;

    @Autowired
    FilesRepository filesRepository;

    @Autowired
    UsersRepository usersRepository;

    public String saveOriginalFile(MultipartFile file, Users user, String taskId) {

        String savedName = taskId + "_" + file.getOriginalFilename();
        File saveFile = new File(fileDir, savedName);

        try {
            file.transferTo(saveFile);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        Files files = Files.builder()
                .taskId(taskId)
                .originalFileName(file.getOriginalFilename())
                .savedFileName(savedName)
                .savedPath(saveFile.getAbsolutePath())
                .createdAt(LocalDateTime.now())
                .size(file.getSize())
                .user(user)   // ★ user 엔티티 연결
                .build();

        filesRepository.save(files);

        // sendToPythonServer(saveFile.getAbsolutePath()); // 중복 호출 제거 - AiService에서 처리함

        return saveFile.getAbsolutePath();
    }

    private void sendToPythonServer(String filePath) {
        RestTemplate restTemplate = new RestTemplate();

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(filePath));
        // Determine basic fileType by extension
        String fileType = "other";
        String lower = filePath.toLowerCase();
        if (lower.endsWith(".mp4") || lower.endsWith(".mov") || lower.endsWith(".mkv") || lower.endsWith(".avi")) {
            fileType = "video";
        } else if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".bmp") || lower.endsWith(".gif")) {
            fileType = "image";
        } else if (lower.endsWith(".wav") || lower.endsWith(".mp3") || lower.endsWith(".flac")) {
            fileType = "audio";
        }
        body.add("fileType", fileType);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> requestEntity =
                new HttpEntity<>(body, headers);

        // Use the unified processing endpoint which handles image/video logic
        String pythonServerUrl = "http://localhost:5000/api/v1/process-file";

        try {
            ResponseEntity<String> response =
                    restTemplate.postForEntity(pythonServerUrl, requestEntity, String.class);

            System.out.println("Python Response: " + response.getBody());
        } catch (Exception e) {
            System.out.println("Python 서버 연결 실패!");
            e.printStackTrace();
        }
    }
}
