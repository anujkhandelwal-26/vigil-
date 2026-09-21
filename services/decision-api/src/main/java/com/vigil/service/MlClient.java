package com.vigil.service;

import com.vigil.api.dto.MlScoreRequest;
import com.vigil.api.dto.MlScoreResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * The single call to ml-service on the hot path. Graceful degradation:
 * if ml-service doesn't answer within the configured timeout (or errors),
 * this returns a rules-only decision with degraded=true rather than
 * propagating the failure -- see docs/architecture.md "Deliberately off
 * the hot path".
 */
@Service
public class MlClient {

    private static final Logger log = LoggerFactory.getLogger(MlClient.class);

    private final RestClient mlScoreRestClient;
    private final RestClient mlLlmRestClient;

    public MlClient(RestClient mlScoreRestClient, RestClient mlLlmRestClient) {
        this.mlScoreRestClient = mlScoreRestClient;
        this.mlLlmRestClient = mlLlmRestClient;
    }

    public record ScoreOutcome(MlScoreResponse response, boolean degraded) {}

    public ScoreOutcome score(MlScoreRequest request) {
        try {
            MlScoreResponse resp = mlScoreRestClient.post()
                    .uri("/internal/score")
                    .body(request)
                    .retrieve()
                    .body(MlScoreResponse.class);
            return new ScoreOutcome(resp, false);
        } catch (Exception e) {
            log.warn("ml-service /internal/score unavailable, falling back to rules-only: {}", e.toString());
            return new ScoreOutcome(null, true);
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> narrative(String applicationId) {
        return mlLlmRestClient.post()
                .uri(uriBuilder -> uriBuilder.path("/internal/narrative")
                        .queryParam("application_id", applicationId).build())
                .retrieve()
                .body(Map.class);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> copilot(String applicationId, String question) {
        return mlLlmRestClient.post()
                .uri("/internal/copilot")
                .body(Map.of("application_id", applicationId, "question", question))
                .retrieve()
                .body(Map.class);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> retrain() {
        return mlLlmRestClient.post()
                .uri("/internal/retrain")
                .retrieve()
                .body(Map.class);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getRing(String applicationId) {
        return mlLlmRestClient.get()
                .uri("/internal/rings/{id}", applicationId)
                .retrieve()
                .body(Map.class);
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getCostCurve() {
        return mlLlmRestClient.get()
                .uri("/internal/metrics/cost-curve")
                .retrieve()
                .body(Map.class);
    }
}
