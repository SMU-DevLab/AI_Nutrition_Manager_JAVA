package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "allergen")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Allergen {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String code;
    private String name;
}

