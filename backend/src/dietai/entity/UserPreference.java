package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "user_preference")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPreference {
    @Id
    private Long memberId;

    @OneToOne
    @MapsId
    @JoinColumn(name = "member_id")
    private Member member;

    private String dietCodes; // comma separated or JSON
    private String excludedCategories;
    private String mealSchedule;
}

