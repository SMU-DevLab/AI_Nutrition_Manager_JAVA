package dietai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MenuRecommendationDto {
    private String menu_name;
    private List<String> used_ingredients;
    private List<String> used_condiments;
    private Integer estimated_calories;
    private String recipe_description;
}

