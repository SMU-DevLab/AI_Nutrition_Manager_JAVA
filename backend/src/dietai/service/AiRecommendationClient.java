package dietai.service;

import dietai.dto.DietRequestDto;
import dietai.dto.DietResponseDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;

@Component
public class AiRecommendationClient {

    private final RestTemplate restTemplate;
    private final String aiApiUrl;

    public AiRecommendationClient(
            @Value("${ai.api.url:http://localhost:8000/api/recommend}") String aiApiUrl) {
        this.restTemplate = new RestTemplate();
        this.aiApiUrl = aiApiUrl;
    }

    public DietResponseDto requestRecommendation(DietRequestDto requestDto) {
        ResponseEntity<DietResponseDto> response = restTemplate.postForEntity(
                aiApiUrl, requestDto, DietResponseDto.class);
        return response.getBody();
    }
}

