package com.vigil.api;

import com.vigil.api.dto.CopilotQueryRequest;
import com.vigil.service.MlClient;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * Thin passthrough to ml-service's RAG copilot. decision-api's job here is
 * authZ (only ANALYST/ADMIN, enforced in SecurityConfig) and nothing else
 * -- the retrieval, grounding and guardrails all live in ml-service.
 */
@RestController
@RequestMapping("/api/v1/copilot")
public class CopilotController {

    private final MlClient mlClient;

    public CopilotController(MlClient mlClient) {
        this.mlClient = mlClient;
    }

    @PostMapping("/query")
    public Map<String, Object> query(@Valid @RequestBody CopilotQueryRequest req) {
        return mlClient.copilot(req.applicationId(), req.question());
    }
}
