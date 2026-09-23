package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "food")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Food {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private FoodCategory category;

    private String name;
    private String foodKind;
    private Double basisGrams;
    private String allergenReview;
}

