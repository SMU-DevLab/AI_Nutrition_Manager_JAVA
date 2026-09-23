package dietai.repository;

import dietai.entity.PantryItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PantryItemRepository extends JpaRepository<PantryItem, Long> {
    List<PantryItem> findByMemberId(Long memberId);
}

