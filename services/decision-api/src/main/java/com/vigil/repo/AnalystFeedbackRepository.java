package com.vigil.repo;

import com.vigil.domain.AnalystFeedback;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface AnalystFeedbackRepository extends JpaRepository<AnalystFeedback, UUID> {
    List<AnalystFeedback> findByApplicationIdOrderByCreatedAtDesc(UUID applicationId);
}
