package com.example.deepflect.Service;


import com.example.deepflect.Entity.Files;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.File;

@Service
@RequiredArgsConstructor
public class AiService {
    @Value("${ai.server.url}")
    private String aiServerUrl;

    @Autowired
    RestTemplate restTemplate;

    /**
     * Python 서버에 노이즈 처리 요청
     * @param taskId 업로드 작업 ID
     * @param filePath 저장된 원본 파일 경로
     */
    public void requestNoiseProcessing(String taskId, String filePath) {

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("taskId", taskId);
        body.add("file", new FileSystemResource(new File(filePath)));

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        HttpEntity<MultiValueMap<String, Object>> requestEntity =
                new HttpEntity<>(body, headers);

        restTemplate.postForEntity(
                aiServerUrl + "/noise",
                requestEntity,
                String.class
        );
    }

}
