package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "recipe_step")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@IdClass(RecipeStepId.class)
public class RecipeStep {
    @Id
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "recipe_id")
    private Recipe recipe;

    @Id
    private Integer stepNo;

    private String instruction;
}

