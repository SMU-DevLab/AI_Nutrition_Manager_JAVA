package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "recipe")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Recipe {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id")
    private Member member;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "job_id")
    private RecommendationJob job;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_recipe_id")
    private Recipe parentRecipe;

    private String title;
    private Integer servings;
    private Double totalGrams;
    private String status;
}

