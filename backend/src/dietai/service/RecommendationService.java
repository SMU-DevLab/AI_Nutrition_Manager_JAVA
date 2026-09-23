package dietai.service;

import dietai.dto.DietRequestDto;
import dietai.dto.DietResponseDto;
import dietai.dto.MenuRecommendationDto;
import dietai.entity.*;
import dietai.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RecommendationService {

    private final MemberRepository memberRepository;
    private final PantryItemRepository pantryItemRepository;
    private final RecommendationJobRepository recommendationJobRepository;
    private final RecipeRepository recipeRepository;
    private final AiRecommendationClient aiRecommendationClient;

    @Transactional
    public DietResponseDto generateRecommendation(Long memberId) {
        Member member = memberRepository.findById(memberId)
                .orElseThrow(() -> new IllegalArgumentException("Member not found"));

        // 1. ?ъ슜?먯쓽 ?앹옱猷?議고쉶
        List<PantryItem> pantryItems = pantryItemRepository.findByMemberId(memberId);
        List<String> ingredients = pantryItems.stream()
                .map(item -> item.getFood().getName())
                .collect(Collectors.toList());

        // 議곕?猷??깆? 異붽? 議고쉶(?ㅺ퀎???앸왂 ?먮뒗 湲곕낯媛??ъ슜)
        List<String> condiments = List.of("?뚭툑", "媛꾩옣", "?꾩텛"); 
        
        // 2. AI ?쒕쾭 ?붿껌 DTO 援ъ꽦
        DietRequestDto requestDto = DietRequestDto.builder()
                .ingredients(ingredients)
                .condiments(condiments)
                .target_calories(500) // ?ъ슜??紐⑺몴 ?곗씠?곗뿉??議고쉶?????덉쓬
                .allergies(List.of()) // ?뚮윭吏 ?곗씠?곗뿉??議고쉶?????덉쓬
                .build();

        // 3. AI 異붿쿇 ?붿껌
        DietResponseDto responseDto = aiRecommendationClient.requestRecommendation(requestDto);

        // 4. Recommendation Job ?앹꽦 諛????        RecommendationJob job = RecommendationJob.builder()
                .member(member)
                .status("COMPLETED")
                .build();
        recommendationJobRepository.save(job);

        // 5. 異붿쿇???덉떆??DB ???        if (responseDto != null && responseDto.getRecommendations() != null) {
            for (MenuRecommendationDto menu : responseDto.getRecommendations()) {
                Recipe recipe = Recipe.builder()
                        .member(member)
                        .job(job)
                        .title(menu.getMenu_name())
                        .status("ACTIVE")
                        // 移쇰줈由??깆? 蹂꾨룄 ?뷀떚?곗뿉 ??ν븷 ???덉쓬 (ERD 李몄“)
                        .build();
                recipeRepository.save(recipe);
                // RecipeIngredient ??異붽? ???媛??            }
        }

        return responseDto;
    }
}

