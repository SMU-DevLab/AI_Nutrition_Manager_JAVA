package dietai.controller;

import dietai.dto.DietResponseDto;
import dietai.service.RecommendationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/recommendations")
@RequiredArgsConstructor
public class RecommendationController {

    private final RecommendationService recommendationService;

    @PostMapping("/{memberId}")
    public ResponseEntity<DietResponseDto> generateRecommendation(@PathVariable Long memberId) {
        DietResponseDto response = recommendationService.generateRecommendation(memberId);
        return ResponseEntity.ok(response);
    }
}

