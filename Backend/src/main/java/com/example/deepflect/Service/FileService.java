package com.example.deepflect.Service;

import com.example.deepflect.Entity.FileType;
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

    // [이동] Controller에서 가져옴
    @Value("${file.output_dir}")
    private String outputDir;

    @Autowired
    FilesRepository filesRepository;

    @Autowired
    UsersRepository usersRepository;

    public String saveOriginalFile(MultipartFile file, Users user, String taskId) {

        // [수정 1] 파일 저장 경로(폴더)가 없으면 자동으로 생성하는 로직 추가
        File directory = new File(fileDir);
        if (!directory.exists()) {
            boolean created = directory.mkdirs(); // mkdirs는 상위 폴더가 없으면 같이 생성해줍니다.
            if (created) {
                log.info("업로드 폴더가 생성되었습니다: {}", directory.getAbsolutePath());
            }
        }

        String savedName = taskId + "_" + file.getOriginalFilename();
        // directory 변수를 사용하여 경로 결합
        File saveFile = new File(directory, savedName);

        try {
            file.transferTo(saveFile);
        } catch (Exception e) {
            log.error("파일 저장 실패", e); // 에러 로그 추가
            throw new RuntimeException("파일 저장 중 오류가 발생했습니다.", e);
        }

        Files files = Files.builder()
                .taskId(taskId)
                .originalFileName(file.getOriginalFilename())
                .savedFileName(savedName)
                .savedPath(saveFile.getAbsolutePath())
                .createdAt(LocalDateTime.now())
                .size(file.getSize())
                .user(user)
                .build();

        filesRepository.save(files);

        // sendToPythonServer(saveFile.getAbsolutePath()); // 중복 호출 제거됨

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

    public File findProtectedFile(String taskId) {
        File[] possibleFiles = {
                new File(outputDir, taskId + "_protected.png"),
                new File(outputDir, taskId + "_protected.jpg"),
                new File(outputDir, taskId + "_protected.jpeg"),
                new File(outputDir, taskId + "_protected.webp"),
                new File(outputDir, taskId + "_protected.mp4"),
                new File(outputDir, taskId + "_protected.wav")
        };

        for (File f : possibleFiles) {
            if (f.exists()) return f;
        }
        return null;
    }

    public boolean deleteProtectedFiles(String taskId) {
        File[] possibleFiles = {
                new File(outputDir, taskId + "_protected.png"),
                new File(outputDir, taskId + "_protected.jpg"),
                new File(outputDir, taskId + "_protected.jpeg"),
                new File(outputDir, taskId + "_protected.webp"),
                new File(outputDir, taskId + "_protected.mp4"),
                new File(outputDir, taskId + "_protected.wav")
        };

        boolean deleted = false;
        for (File f : possibleFiles) {
            if (f.exists()) {
                if (f.delete()) {
                    log.info("Deleted protected file: {}", f.getAbsolutePath());
                    deleted = true;
                }
            }
        }
        return deleted;
    }

    // [이동 & 변경] private -> public, static으로 만들어도 무방함
    public FileType determineFileType(String fileName) {
        if (fileName == null) return FileType.UNKNOWN;
        String lowerName = fileName.toLowerCase();

        if (lowerName.endsWith(".mp4") || lowerName.endsWith(".mov") || lowerName.endsWith(".mkv") || lowerName.endsWith(".avi")) {
            return FileType.VIDEO;
        } else if (lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg") || lowerName.endsWith(".png") || lowerName.endsWith(".bmp") || lowerName.endsWith(".gif") || lowerName.endsWith(".webp")) {
            return FileType.IMAGE;
        }
        return FileType.UNKNOWN;
    }

    // [추가 제안] listFiles 로직도 서비스에 있는게 맞습니다.
    public File getOutputDirectory() {
        return new File(outputDir);
    }
}