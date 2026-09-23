package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "food_category")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class FoodCategory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String code;
    private String name;
}

