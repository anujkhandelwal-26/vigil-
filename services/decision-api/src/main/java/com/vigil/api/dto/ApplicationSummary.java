package com.vigil.api.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

public record ApplicationSummary(
        UUID id,
        String externalRef,
        OffsetDateTime submittedAt,
        String product,
        BigDecimal amountInr,
        String action,
        BigDecimal riskScore,
        Integer latencyMs
) {}
