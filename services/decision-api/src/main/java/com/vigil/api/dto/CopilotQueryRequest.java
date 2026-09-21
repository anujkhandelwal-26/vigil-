package com.vigil.api.dto;

import jakarta.validation.constraints.NotBlank;

public record CopilotQueryRequest(@NotBlank String applicationId, @NotBlank String question) {}
