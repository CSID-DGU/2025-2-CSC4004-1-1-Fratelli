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
        uploadProgressService.saveUpload(uploadMeta);
        
        aiService.requestNoiseProcessing(taskId, savedPath);

        return ResponseEntity.ok(taskId);
    }

    @GetMapping("/download/{taskId}/{fileName}")
    public ResponseEntity<Resource> download(@PathVariable("taskId") String taskId, @PathVariable("fileName") String fileName) {
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

    @GetMapping("/download-protected/{taskId}")
    public ResponseEntity<Resource> downloadProtected(@PathVariable("taskId") String taskId) {
        try {
            System.out.println("[FileController] Downloading protected file for taskId: " + taskId);
            
            // Python 서버의 outputs 폴더에서 보호된 파일 찾기
            String pythonOutputsDir = "C:\\Users\\betty\\2025-2-CSC4004-1-1-Fratelli\\AI\\temp\\outputs";
            
            // 확장자 시도(우선 이미지 -> 영상 -> 음성)
            File[] possibleFiles = {
                new File(pythonOutputsDir + "\\" + taskId + "_protected.png"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpeg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.webp"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.mp4"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.wav")
            };
            
            File protectedFile = null;
            for (File f : possibleFiles) {
                System.out.println("[FileController] Checking: " + f.getAbsolutePath() + " exists=" + f.exists());
                if (f.exists()) {
                    protectedFile = f;
                    System.out.println("[FileController] Found file: " + f.getAbsolutePath());
                    break;
                }
            }
            
            if (protectedFile == null) {
                System.out.println("[FileController] No protected file found for taskId: " + taskId);
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(null);
            }
            
            // 파일 타입 판단 (이미지/비디오/오디오)
            String name = protectedFile.getName().toLowerCase();
            String contentType;
            String fileName;
            if (name.endsWith(".png")) {
                contentType = "image/png";
                fileName = "protected_" + taskId + ".png";
            } else if (name.endsWith(".jpg") || name.endsWith(".jpeg")) {
                contentType = "image/jpeg";
                fileName = "protected_" + taskId + ".jpg";
            } else if (name.endsWith(".webp")) {
                contentType = "image/webp";
                fileName = "protected_" + taskId + ".webp";
            } else if (name.endsWith(".mp4")) {
                contentType = "video/mp4";
                fileName = "protected_" + taskId + ".mp4";
            } else {
                // 기본으로 wav 처리 (과거 호환성 유지)
                contentType = "audio/wav";
                fileName = "protected_" + taskId + ".wav";
            }
            
            Resource resource = new FileSystemResource(protectedFile);
            System.out.println("[FileController] Sending file: " + fileName + " contentType=" + contentType);
            
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + fileName + "\"")
                    .contentType(MediaType.parseMediaType(contentType))
                    .body(resource);
                    
        } catch (Exception e) {
            System.out.println("[FileController] Error downloading file: " + e.getMessage());
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
    @GetMapping("/upload-status/{tempFileID}")
    public ResponseEntity<?> getUploadStatus(@PathVariable("tempFileID") String tempFileID) {
        var st = uploadProgressService.getStatus(tempFileID);
        if (st == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", "no status for tempFileID"));
        }
        return ResponseEntity.ok(st);
    }

    // 업로드 중인 파일 목록 (type 필터링 지원)
    @GetMapping("/uploads")
    public ResponseEntity<FileUploadListResponse> getUploads(
            @RequestParam(value = "type", required = false) FileType type) {

        var uploads = uploadProgressService.listUploads();

        // 진행률 기반 상태 업데이트
        for (FileUploadResponse upload : uploads) {
            if (upload.getTaskId() != null) {
                int progress = progressService.getProgress(upload.getTaskId());

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

//    @GetMapping("/uploads")
//    public ResponseEntity<FileUploadListResponse> getUploads(
//            @RequestParam(value = "type", required = false) FileType type) {
//        var uploads = uploadProgressService.listUploads();
//
//        // 각 업로드에 대해 진행률 기반 상태 업데이트
//        for (FileUploadResponse upload : uploads) {
//            if (upload.getTaskId() != null) {
//                int progress = progressService.getProgress(upload.getTaskId());
//
//                // 실패 여부 확인 후 상태 업데이트
//                if (progressService.isFailed(upload.getTaskId())) {
//                    upload.setStatus(Status.FAILED);
//                } else if (progress >= 100) {
//                    upload.setStatus(Status.SUCCESS);
//                } else {
//                    upload.setStatus(Status.UPLOADING);
//                }
//            }
//        }
//
//        // type 파라미터로 필터링
//        if (type != null) {
//            uploads = uploads.stream()
//                    .filter(u -> u.getFileType() == type)
//                    .collect(java.util.stream.Collectors.toList());
//        }
//
//        var resp = new FileUploadListResponse(uploads);
//        return ResponseEntity.ok(resp);
//    }

    @GetMapping
    public ResponseEntity<FileListResponse> listFiles(@RequestParam(value = "type", required = false) FileType type) {
        try {
            // Python outputs 폴더에서 처리 완료된 파일 스캔
            String pythonOutputsDir = "C:\\Users\\betty\\2025-2-CSC4004-1-1-Fratelli\\AI\\temp\\outputs";
            File outputsFolder = new File(pythonOutputsDir);
            
            java.util.List<FilesDTO> filesList = new java.util.ArrayList<>();
            
            if (outputsFolder.exists() && outputsFolder.isDirectory()) {
                File[] files = outputsFolder.listFiles((dir, name) -> name.contains("_protected."));
                
                if (files != null) {
                    for (File f : files) {
                        // 파일명에서 taskId 추출 (예: taskId_protected.mp4 -> taskId)
                        String fileName = f.getName();
                        String taskId = fileName.substring(0, fileName.indexOf("_protected"));
                        
                        // 파일 타입 감지
                        String nameLower = fileName.toLowerCase();
                        FileType fileType;
                        if (nameLower.endsWith(".png") || nameLower.endsWith(".jpg") || 
                            nameLower.endsWith(".jpeg") || nameLower.endsWith(".webp")) {
                            fileType = FileType.IMAGE;
                        } else if (nameLower.endsWith(".mp4")) {
                            fileType = FileType.VIDEO;
                        } else {
                            fileType = FileType.UNKNOWN;
                        }

                        // type: FileType enum
                        if (type != null && fileType != type) {
                            continue;
                        }

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
            
            FileListResponse resp = new FileListResponse(filesList);
            return ResponseEntity.ok(resp);
            
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new FileListResponse(new java.util.ArrayList<>()));
        }
    }

    // 결과 다운로드
    @GetMapping("/{taskId}/download")
    public ResponseEntity<ResultDownloadResponse> getResultDownload(@PathVariable("taskId") String taskId) {
        try {
            // Check if processing is completed
            if (!downloadService.isCompleted(taskId)) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(new ResultDownloadResponse(taskId, null, null, 0L, null, "File not ready yet", null));
            }

            // Python outputs 폴더에서 보호된 파일 찾기
            String pythonOutputsDir = "C:\\Users\\betty\\2025-2-CSC4004-1-1-Fratelli\\AI\\temp\\outputs";
            
            File[] possibleFiles = {
                new File(pythonOutputsDir + "\\" + taskId + "_protected.png"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpeg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.webp"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.mp4"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.wav")
            };
            
            File protectedFile = null;
            for (File f : possibleFiles) {
                if (f.exists()) {
                    protectedFile = f;
                    break;
                }
            }
            
            if (protectedFile == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(new ResultDownloadResponse(taskId, null, null, 0L, null, "Protected file not found", null));
            }

            // 파일 정보 추출
            String fileName = protectedFile.getName();
            FileType fileType;
            String nameLower = fileName.toLowerCase();
            if (nameLower.endsWith(".png") || nameLower.endsWith(".jpg") || nameLower.endsWith(".jpeg") || nameLower.endsWith(".webp")) {
                fileType = FileType.IMAGE;
            } else if (nameLower.endsWith(".mp4")) {
                fileType = FileType.VIDEO;
            } else {
                fileType = FileType.UNKNOWN;
            }

            long size = protectedFile.length();
            String downloadUrl = "http://localhost:8080/api/v1/files/download-protected/" + taskId;
            Timestamp timestamp = Timestamp.from(java.time.Instant.now());

            ResultDownloadResponse resp = new ResultDownloadResponse(
                taskId, 
                fileName, 
                fileType, 
                size, 
                downloadUrl, 
                "File ready for download", 
                timestamp
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
    public ResponseEntity<?> handleUploadResponse(@RequestBody com.example.deepflect.DTO.FileUploadResponse uploadResp) {
        try {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            UserDetails userDetails = (UserDetails) auth.getPrincipal();

            // 이메일로 Users 엔티티 조회
            Users user = usersRepository.findByEmail(userDetails.getUsername())
                    .orElseThrow(() -> new RuntimeException("User not found"));

            System.out.println("[FileController] Received upload-response: taskId=" + uploadResp.getTaskId() + ", fileName=" + uploadResp.getFileName() + ", status=" + uploadResp.getStatus());

            // Check local expected file path (user-scoped storage)
            String userFolderPath = fileDir + "/" + user.getEmail();
            String expectedPath = userFolderPath + "/" + uploadResp.getTaskId() + "_" + uploadResp.getFileName();
            File f = new File(expectedPath);

            if (f.exists()) {
                System.out.println("[FileController] Found local file for taskId=" + uploadResp.getTaskId() + ", starting AI processing: " + expectedPath);
                // Trigger AI processing using existing path
                aiService.requestNoiseProcessing(uploadResp.getTaskId(), expectedPath);
                // store upload metadata for listing
                uploadProgressService.saveUpload(uploadResp);
                return ResponseEntity.ok(Map.of("taskId", uploadResp.getTaskId(), "processed", true));
            } else {
                System.out.println("[FileController] Local file not found for taskId=" + uploadResp.getTaskId() + ", expected=" + expectedPath);
                // Accept and store metadata for later processing (not implemented: DB save)
                // still store metadata so /uploads can show it
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
            
            // 원본 파일 삭제 (uploads 폴더)
            String userFolderPath = fileDir + "/" + user.getEmail();
            String uploadedFilePath = userFolderPath + "/" + taskId + "_" + upload.getFileName();
            File uploadedFile = new File(uploadedFilePath);
            if (uploadedFile.exists()) {
                uploadedFile.delete();
                System.out.println("[FileController] Deleted uploaded file: " + uploadedFilePath);
            }
            
            // 진행 중이던 보호된 파일도 삭제 (outputs 폴더)
            String pythonOutputsDir = "C:\\Users\\betty\\2025-2-CSC4004-1-1-Fratelli\\AI\\temp\\outputs";
            File[] possibleFiles = {
                new File(pythonOutputsDir + "\\" + taskId + "_protected.png"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpeg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.webp"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.mp4")
            };
            for (File f : possibleFiles) {
                if (f.exists()) {
                    f.delete();
                    System.out.println("[FileController] Deleted protected file: " + f.getAbsolutePath());
                }
            }
            
            // AI 서버에 취소 요청 전송
            try {
                aiService.cancelProcessing(taskId);
                System.out.println("[FileController] AI processing cancellation requested for taskId: " + taskId);
            } catch (Exception e) {
                System.out.println("[FileController] Failed to cancel AI processing: " + e.getMessage());
            }
            
            // 메타데이터 삭제
            uploadProgressService.deleteUpload(taskId);
            progressService.updateProgress(taskId, 0); // 진행률 초기화
            
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
            // Python outputs 폴더에서 보호된 파일 찾아서 삭제
            String pythonOutputsDir = "C:\\Users\\betty\\2025-2-CSC4004-1-1-Fratelli\\AI\\temp\\outputs";
            
            File[] possibleFiles = {
                new File(pythonOutputsDir + "\\" + taskId + "_protected.png"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.jpeg"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.webp"),
                new File(pythonOutputsDir + "\\" + taskId + "_protected.mp4")
            };
            
            boolean deleted = false;
            for (File f : possibleFiles) {
                if (f.exists()) {
                    f.delete();
                    System.out.println("[FileController] Deleted result file: " + f.getAbsolutePath());
                    deleted = true;
                }
            }
            
            if (!deleted) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(Map.of("message", "Result file not found", "status", 404));
            }
            
            // 다운로드 URL 정보 삭제
//            downloadService.saveDownloadUrl(taskId, null);
            
            return ResponseEntity.ok(Map.of("message", "Result deleted", "status", 200));
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", e.getMessage(), "status", 500));
        }
    }

}
