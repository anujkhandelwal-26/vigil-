package com.vigil.repo;

import com.vigil.domain.Decision;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface DecisionRepository extends JpaRepository<Decision, UUID> {

    Optional<Decision> findFirstByApplicationIdOrderByCreatedAtDesc(UUID applicationId);

    List<Decision> findTop200ByOrderByCreatedAtDesc();

    @Query("SELECT COUNT(d) FROM Decision d WHERE d.createdAt > :since")
    long countSince(@Param("since") java.time.OffsetDateTime since);

    @Query("SELECT d.action, COUNT(d) FROM Decision d WHERE d.createdAt > :since GROUP BY d.action")
    List<Object[]> countByActionSince(@Param("since") java.time.OffsetDateTime since);
}
