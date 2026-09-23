package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "member_allergy")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemberAllergy {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id")
    private Member member;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "allergen_id")
    private Allergen allergen;

    private String customText;
    private String status;
}

