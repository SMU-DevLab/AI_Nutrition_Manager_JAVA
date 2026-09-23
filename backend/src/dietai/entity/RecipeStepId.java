package dietai.entity;

import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;

@Getter
@Setter
@EqualsAndHashCode
public class RecipeStepId implements Serializable {
    private Long recipe;
    private Integer stepNo;
}

