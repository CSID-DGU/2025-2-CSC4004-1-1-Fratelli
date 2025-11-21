package com.example.deepflect.Controller;

import com.example.deepflect.DTO.FileUploadRequest;
import com.example.deepflect.DTO.FileUploadResponse;
import com.example.deepflect.DTO.FilesDTO;
import com.example.deepflect.DTO.ProgressDTO;
import com.example.deepflect.DTO.FileUploadStatusResponse;
import com.example.deepflect.DTO.FileUploadListResponse;
import com.example.deepflect.DTO.FileListResponse;
import com.example.deepflect.DTO.ResultDownloadResponse;
import com.example.deepflect.Entity.FileType;
import com.example.deepflect.Entity.Files;
import com.example.deepflect.Entity.Status;
import com.example.deepflect.Entity.Users;
import com.example.deepflect.Repository.UsersRepository;
import com.example.deepflect.Service.AiService;
import com.example.deepflect.Service.ProgressService;
import com.example.deepflect.Service.ProgressManager;
import org.springframework.core.io.Resource;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import com.example.deepflect.Service.FileService;
import com.example.deepflect.Service.DownloadService;
import com.example.deepflect.Service.UploadProgressService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.sql.Timestamp;
import java.util.UUID;
import java.util.Map;

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

    @Autowired
    ProgressManager progressManager;

    @Autowired
    DownloadService downloadService;

    @Autowired
    UploadProgressService uploadProgressService;

    @Value("${file.dir}")
    private String fileDir;

    @Value("${file.output_dir}")
    private String outputDir;

    @PostMapping(value = {"/upload", "/uploads"}, consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> upload(@RequestParam("file") MultipartFile file,
                                         @RequestParam(value = "type", required = false) String type) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        UserDetails userDetails = (UserDetails) auth.getPrincipal();

        // 이메일로 Users 엔티티 조회
        Users user = usersRepository.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        // 업로드 폴더 생성 (uploadedFiles/user_email)
        // [수정 2] 경로 생성 시 File 객체 활용 (OS 호환성 확보)
        File folder = new File(fileDir, user.getEmail());
//        String userFolderPath = fileDir + "/" + user.getEmail(); // fileDir = /Users/betty/OSS_team1/uploadedFiles
//        File folder = new File(userFolderPath);
        if (!folder.exists()) {
            folder.mkdirs(); // 상위 폴더까지 생성
        }

        String taskId = UUID.randomUUID().toString();
        String savedPath = fileService.saveOriginalFile(file, user, taskId);

        // 업로드 메타데이터 저장
        String fileName = file.getOriginalFilename();
        String lower = fileName != null ? fileName.toLowerCase() : "";
        FileType fileType;
        if (lower.endsWith(".mp4") || lower.endsWith(".mov") || lower.endsWith(".mkv") || lower.endsWith(".avi")) {
            fileType = FileType.VIDEO;
        } else if (lower.endsWith(".jpg") || lower.endsWith(".jpeg") || lower.endsWith(".png") || lower.endsWith(".bmp") || lower.endsWith(".gif")) {
            fileType = FileType.IMAGE;
        } else
            fileType = FileType.UNKNOWN;

        FileUploadResponse uploadMeta = new FileUploadResponse(
            taskId,
            fileName,
            file.getSize(),
            fileType,
            Status.UPLOADING,
            Timestamp.from(java.time.Instant.now())
        );
        uploadMeta.setUserEmail(user.getEmail());
        uploadProgressService.saveUpload(uploadMeta);

        aiService.requestNoiseProcessing(taskId, savedPath);

        return ResponseEntity.ok(uploadMeta);
//        return ResponseEntity.ok(taskId);
    }

    @GetMapping("/download/{taskId}/{fileName}")
    public ResponseEntity<Resource> download(@PathVariable("taskId") String taskId, @PathVariable("fileName") String fileName) {
        // [수정 3] 하드코딩된 문자열 결합 대신 File 생성자 사용
        File file = new File(fileDir, taskId + "_" + fileName);
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }

        Resource resource = new FileSystemResource(file);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getName() + "\"")
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .body(resource);
    }

    @GetMapping("/download-protected/{taskId}")
    public ResponseEntity<Resource> downloadProtected(@PathVariable("taskId") String taskId) {
        try {
            System.out.println("[FileController] Downloading protected file for taskId: " + taskId);

            // [수정] 헬퍼 메서드로 파일 찾기 (outputDir 사용)
            File protectedFile = fileService.findProtectedFile(taskId);

            if (protectedFile == null) {
                System.out.println("[FileController] No protected file found for taskId: " + taskId);
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
            }

            String fileName = protectedFile.getName();
            // [변경] Service 호출
            FileType fileType = fileService.determineFileType(fileName);

            // 컨텐츠 타입 결정 로직 (이것도 사실 서비스나 유틸로 빼면 좋음)
            String contentType;
            if (fileType == FileType.IMAGE) {
                if (fileName.endsWith(".png")) contentType = "image/png";
                else if (fileName.endsWith(".webp")) contentType = "image/webp";
                else contentType = "image/jpeg";
            } else if (fileType == FileType.VIDEO) {
                contentType = "video/mp4";
            } else {
                contentType = "audio/wav";
            }

            Resource resource = new FileSystemResource(protectedFile);
            System.out.println("[FileController] Sending file: " + fileName + " contentType=" + contentType);

            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + fileName + "\"")
                    .contentType(MediaType.parseMediaType(contentType))
                    .body(resource);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/status/{taskId}")
    public ResponseEntity<?> getStatus(@PathVariable("taskId") String taskId) {
        try {
            var status = aiService.getProtectionStatus(taskId);
            return ResponseEntity.ok(status);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error getting status: " + e.getMessage());
        }
    }

    @GetMapping("/progress/{taskId}")
    public ResponseEntity<?> getProgress(@PathVariable("taskId") String taskId) {
        try {
            int progress = progressService.getProgress(taskId);
            return ResponseEntity.ok(Map.of("taskId", taskId, "progress", progress));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error: " + e.getMessage());
        }
    }

    @GetMapping("/completion-status/{taskId}")
    public ResponseEntity<?> getCompletionStatus(@PathVariable("taskId") String taskId) {
        try {
            int progress = progressService.getProgress(taskId);
            boolean isCompleted = downloadService.isCompleted(taskId);
            String downloadUrl = null;

            if (isCompleted) {
                downloadUrl = downloadService.getDownloadUrl(taskId);
            }

            return ResponseEntity.ok(Map.of(
                    "taskId", taskId,
                    "progress", progress,
                    "isCompleted", isCompleted,
                    "downloadUrl", downloadUrl != null ? downloadUrl : ""
            ));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error: " + e.getMessage());
        }
    }

    @GetMapping(value = "/progress-stream/{taskId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamProgress(@PathVariable("taskId") String taskId) {
        SseEmitter emitter = new SseEmitter(300000L); // 5-minute timeout
        progressManager.addEmitter(taskId, emitter);
        try {
            emitter.send(SseEmitter.event().name("start").data("Progress stream started"));
        } catch (Exception e) {
            try {
                emitter.completeWithError(e);
            } catch (Exception ignored) {}
        }
        return emitter;
    }

    // --- Mock endpoints to return the requested response shapes ---
    @GetMapping("/upload-status/{taskId}")
    public ResponseEntity<?> getUploadStatus(@PathVariable("taskId") String taskId) {
        var st = uploadProgressService.getStatus(taskId);
        if (st == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "no status for taskId"));
        }
        return ResponseEntity.ok(st);
    }

    // 업로드 중인 파일 목록 (type 필터링 지원)
    @GetMapping("/uploads")
    public ResponseEntity<FileUploadListResponse> getUploads(
            @RequestParam(value = "type", required = false) FileType type) {

        var uploads = uploadProgressService.listUploads();

        // 진행률 기반 상태 및 progress 업데이트
        for (FileUploadResponse upload : uploads) {
            if (upload.getTaskId() != null) {
                int progress = progressService.getProgress(upload.getTaskId());
                upload.setProgress(progress); // 진행률 설정

                if (progressService.isFailed(upload.getTaskId())) {
                    upload.setStatus(Status.FAILED);
                } else if (progress >= 100) {
                    upload.setStatus(Status.SUCCESS);
                } else {
                    upload.setStatus(Status.UPLOADING);
                }
            }
        }

        // 1차 필터링 : 업로드 중(UPLOADING)인 것만 출력
        uploads = uploads.stream()
                .filter(u -> u.getStatus() == Status.UPLOADING)
                .collect(java.util.stream.Collectors.toList());

        // 2차 필터링 : type 파라미터가 있을 경우 해당 fileType만 출력
        if (type != null) {
            uploads = uploads.stream()
                    .filter(u -> u.getFileType() == type)
                    .collect(java.util.stream.Collectors.toList());
        }

        var resp = new FileUploadListResponse(uploads);
        return ResponseEntity.ok(resp);
    }

    @GetMapping
    public ResponseEntity<FileListResponse> listFiles(@RequestParam(value = "type", required = false) FileType type) {
        try {
            // [수정] outputDir 변수 사용
            File outputsFolder = new File(outputDir);

            // 1. outputDir 경로 확인
            System.out.println("========== [DEBUG] listFiles 시작 ==========");
            System.out.println("설정된 outputDir 값: " + outputDir);
            System.out.println("설정된 outputsFolder 값: " + outputsFolder);

            java.util.List<FilesDTO> filesList = new java.util.ArrayList<>();

            if (outputsFolder.exists() && outputsFolder.isDirectory()) {
                File[] files = outputsFolder.listFiles((dir, name) -> name.contains("_protected."));

                if (files != null) {
                    for (File f : files) {
                        String fileName = f.getName();
                        String taskId = fileName.substring(0, fileName.indexOf("_protected"));

                        // 파일 타입 감지 (enum 변환 로직 간소화 가능)
                        String nameLower = fileName.toLowerCase();
                        FileType fileType = fileService.determineFileType(nameLower);

                        if (type != null && fileType != type) continue;

                        FilesDTO dto = new FilesDTO();
                        dto.setTaskId(taskId);
                        dto.setFileName(fileName);
                        dto.setFileType(fileType);
                        dto.setSize(f.length());
                        dto.setUrl("http://localhost:8080/api/v1/files/download-protected/" + taskId);
                        dto.setTimestamp(Timestamp.from(java.time.Instant.ofEpochMilli(f.lastModified())));
                        filesList.add(dto);
                    }
                }
            }
            return ResponseEntity.ok(new FileListResponse(filesList));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new FileListResponse(new java.util.ArrayList<>()));
        }
    }

    // 결과 다운로드
    @GetMapping("/{taskId}/download")
    public ResponseEntity<ResultDownloadResponse> getResultDownload(@PathVariable("taskId") String taskId) {
        try {
            if (!downloadService.isCompleted(taskId)) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(new ResultDownloadResponse(taskId, null, null, 0L, null, "File not ready yet", null));
            }

            // [수정] 헬퍼 메서드 사용
            File protectedFile = fileService.findProtectedFile(taskId);

            if (protectedFile == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(new ResultDownloadResponse(taskId, null, null, 0L, null, "Protected file not found", null));
            }

            String fileName = protectedFile.getName();
            FileType fileType = fileService.determineFileType(fileName.toLowerCase());

            long size = protectedFile.length();
            String downloadUrl = "http://localhost:8080/api/v1/files/download-protected/" + taskId;
            Timestamp timestamp = Timestamp.from(java.time.Instant.now());

            ResultDownloadResponse resp = new ResultDownloadResponse(
                    taskId, fileName, fileType, size, downloadUrl, "File ready for download", timestamp
            );
            return ResponseEntity.ok(resp);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new ResultDownloadResponse(taskId, null, null, 0L, null, "Error: " + e.getMessage(), null));
        }
    }

    @PostMapping(value = "/upload-status", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> postUploadStatus(@RequestBody FileUploadStatusResponse status) {
        try {
            if (status == null || status.getTaskId() == null) {
                return ResponseEntity.badRequest().body(Map.of("message", "invalid payload"));
            }
            uploadProgressService.saveStatus(status);
            return ResponseEntity.ok(Map.of("saved", true, "fileID", status.getTaskId()));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", e.getMessage()));
        }
    }

    @PostMapping(value = "/upload-response", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> handleUploadResponse(@RequestBody FileUploadResponse uploadResp) {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            UserDetails userDetails = (UserDetails) auth.getPrincipal();

            // 이메일로 Users 엔티티 조회
            Users user = usersRepository.findByEmail(userDetails.getUsername())
                    .orElseThrow(() -> new RuntimeException("User not found"));

            System.out.println("[FileController] Received upload-response: taskId=" + uploadResp.getTaskId() + ", fileName=" + uploadResp.getFileName() + ", status=" + uploadResp.getStatus());

            /// [수정] File 객체 사용하여 경로 생성 (OS 호환성)
            File userFolder = new File(fileDir, user.getEmail());
            File expectedFile = new File(userFolder, uploadResp.getTaskId() + "_" + uploadResp.getFileName());
//            File f = new File(expectedPath);

            if (expectedFile.exists()) {
                aiService.requestNoiseProcessing(uploadResp.getTaskId(), expectedFile.getAbsolutePath());
                uploadProgressService.saveUpload(uploadResp);
                return ResponseEntity.ok(Map.of("taskId", uploadResp.getTaskId(), "processed", true));
            } else {
                uploadProgressService.saveUpload(uploadResp);
                return ResponseEntity.status(HttpStatus.ACCEPTED).body(Map.of("taskId", uploadResp.getTaskId(), "processed", false, "message", "file not found locally"));
            }
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", e.getMessage()));
        }
    }

    // 업로드 중인 파일 삭제 (취소)
    @DeleteMapping("/uploads/{taskId}")
    public ResponseEntity<?> deleteUpload(@PathVariable("taskId") String taskId) {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            UserDetails userDetails = (UserDetails) auth.getPrincipal();
            Users user = usersRepository.findByEmail(userDetails.getUsername())
                    .orElseThrow(() -> new RuntimeException("User not found"));

            // 업로드 메타데이터 조회
            FileUploadResponse upload = uploadProgressService.getUpload(taskId);
            if (upload == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(Map.of("message", "Upload not found", "status", 404));
            }

            // [수정] 원본 파일 삭제 경로 File 객체 사용
            File userFolder = new File(fileDir, user.getEmail());
            File uploadedFile = new File(userFolder, taskId + "_" + upload.getFileName());

            if (uploadedFile.exists()) {
                uploadedFile.delete();
                System.out.println("[FileController] Deleted uploaded file: " + uploadedFile.getAbsolutePath());
            }

            // [수정] 결과 파일 삭제 (헬퍼 메서드 사용)
            fileService.deleteProtectedFiles(taskId);

            try { aiService.cancelProcessing(taskId); }
            catch (Exception e) { System.out.println("Failed to cancel: " + e.getMessage()); }

            uploadProgressService.deleteUpload(taskId);
            progressService.updateProgress(taskId, 0);

            return ResponseEntity.ok(Map.of("message", "Upload deleted", "status", 200));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", e.getMessage(), "status", 500));
        }
    }

    // 변환 완료된 결과 파일 삭제
    @DeleteMapping("/{taskId}")
    public ResponseEntity<?> deleteResult(@PathVariable("taskId") String taskId) {
        try {
            // [수정] 헬퍼 메서드 사용
            boolean deleted = fileService.deleteProtectedFiles(taskId);

            if (!deleted) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "Result file not found", "status", 404));
            }
            return ResponseEntity.ok(Map.of("message", "Result deleted", "status", 200));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("message", e.getMessage(), "status", 500));
        }
    }


}
