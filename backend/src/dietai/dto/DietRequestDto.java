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
public class DietRequestDto {
    private List<String> ingredients;
    private List<String> condiments;
    private Integer target_calories;
    private List<String> allergies;
}

