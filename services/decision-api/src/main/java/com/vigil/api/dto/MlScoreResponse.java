package com.vigil.api.dto;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

public record MlScoreResponse(
        BigDecimal riskScore,
        BigDecimal anomalyScore,
        String action,
        List<String> reasonCodes,
        List<Map<String, Object>> shapTop,
        String modelVersion,
        Integer latencyMs
) {}
