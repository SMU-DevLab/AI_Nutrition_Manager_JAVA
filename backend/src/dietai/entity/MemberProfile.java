package dietai.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "member_profile")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MemberProfile {
    @Id
    private Long memberId;

    @OneToOne
    @MapsId
    @JoinColumn(name = "member_id")
    private Member member;

    private Integer birthYear;
    private Double heightCm;
    private String activityCode;
    private String timezone;
}

