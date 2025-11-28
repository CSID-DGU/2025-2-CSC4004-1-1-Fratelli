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

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
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

    public File getOutputDirectory() {
        return new File(outputDir);
    }

    /**
     * [추가] 썸네일 파일 찾기
     * Python 백엔드에서 생성한 {taskId}_protected_thumbnail.jpg 파일을 찾습니다.
     */
    public File findThumbnailFile(String taskId) {
        // 1. Python 코드에서 정한 파일명 규칙: {taskId}_protected_thumbnail.jpg
        File thumbFile = new File(outputDir, taskId + "_protected_thumbnail.jpg");

        if (thumbFile.exists()) {
            return thumbFile;
        }

        // 2. 혹시 protected가 없는 경우 대비 (예비책)
        File fallback = new File(outputDir, taskId + "_thumbnail.jpg");
        if (fallback.exists()) {
            return fallback;
        }

        return null; // 썸네일 없음
    }

    /**
     * [수정] 썸네일 URL 반환
     * 비디오 파일인 경우에만 썸네일 API 주소를 반환합니다.
     */
    public String getThumbnailUrl(String taskId, FileType fileType) {
        // 비디오 파일일 경우에만 썸네일 제공
        if (fileType == FileType.VIDEO) {
            // 실제 파일이 존재하는지 확인 후 URL 반환 (선택 사항)
            File thumb = findThumbnailFile(taskId);

            if (thumb != null && thumb.exists()) {
                String thumbnail2 = "http://localhost:8080/api/v1/files/thumbnail/" + taskId;
                log.info("[FileService] Found thumbnail URL for taskId={}: {}", taskId, thumbnail2);
                return thumbnail2;
            }
        }
        // 이미지는 원본 자체가 썸네일 역할을 하거나, 필요 없다면 null
        return null;
    }

    /**
     * FFmpeg로 영상 첫 프레임을 추출해 JPG 썸네일 생성
     */
    private void generateVideoThumbnail(File videoFile, File thumbnailFile) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(
                "ffmpeg",
                "-i", videoFile.getAbsolutePath(),
                "-ss", "00:00:00", // 시작 프레임
                "-vframes", "1",
                "-q:v", "2",
                thumbnailFile.getAbsolutePath()
        );
        pb.redirectErrorStream(true);
        Process process = pb.start();
        process.waitFor();
    }

//    public String getThumbnailUrl(String taskId, FileType fileType) {
//
//        File file = findProtectedFile(taskId);
//        if (file == null) return null;
//
//        // 이미지이면 thumbnail = 원본 URL 그대로
//        if (fileType.equals("image")) {
//            return "/api/v1/files/download-protected/" + taskId;
//        }
//
//        // 영상이면 첫 프레임 썸네일을 생성해서 반환
//        if (fileType.equals("video")) {
//
//            // 기존 썸네일이 있으면 바로 사용
//            File thumb = findProtectedThumbnail(taskId);
//            if (thumb != null) {
//                return "/files/" + thumb.getName();
//            }
//
//            // 새로 생성
//            File newThumb = generateVideoThumbnail(taskId, file);
//            if (newThumb != null) {
//                return "/files/" + newThumb.getName();
//            }
//        }
//
//        return null;
//    }
}