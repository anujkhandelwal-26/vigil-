package com.vigil.api.dto;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

public record DecisionResponse(
        UUID applicationId,
        String externalRef,
        String action,
        BigDecimal riskScore,
        BigDecimal anomalyScore,
        List<String> reasonCodes,
        String shapTop,
        String modelVersion,
        Integer latencyMs,
        Boolean degraded,
        List<String> verificationSteps,
        String keyFactStatement
) {}
