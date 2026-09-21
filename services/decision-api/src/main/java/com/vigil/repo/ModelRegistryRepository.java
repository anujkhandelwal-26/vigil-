package com.vigil.repo;

import com.vigil.domain.ModelRegistry;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface ModelRegistryRepository extends JpaRepository<ModelRegistry, UUID> {
    List<ModelRegistry> findAllByOrderByTrainedAtDesc();
}
