package dietai.repository;

import dietai.entity.RecommendationJob;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface RecommendationJobRepository extends JpaRepository<RecommendationJob, Long> {
}

