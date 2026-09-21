package com.vigil.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record FeedbackRequest(
        @NotBlank @Pattern(regexp = "FRAUD|LEGIT") String verdict,
        String note
) {}
