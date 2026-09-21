package com.vigil.service;

import com.vigil.api.dto.MlScoreRequest;
import org.junit.jupiter.api.Test;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Pure unit test, no Spring context. Points the RestClient at a port
 * nothing is listening on, so every call fails fast -- proving MlClient
 * degrades gracefully (degraded=true, response=null) instead of
 * propagating the failure to the caller. This is the resilience story
 * behind the ML_UNAVAILABLE_RULES_ONLY reason code.
 */
class MlClientFallbackTest {

    @Test
    void scoreDegradesGracefullyWhenMlServiceIsUnreachable() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(200);
        factory.setReadTimeout(200);
        RestClient unreachable = RestClient.builder()
                .baseUrl("http://localhost:1") // nothing listens on port 1
                .requestFactory(factory)
                .build();

        MlClient client = new MlClient(unreachable, unreachable);
        MlScoreRequest req = new MlScoreRequest(
                "app-id", "APP-TEST", 30, "F", "SALARIED", BigDecimal.valueOf(50000), 2, "560", "RENTED",
                "CONSUMER_DURABLE", BigDecimal.valueOf(50000), 12, "ANDROID_APP",
                720, false, 1, 1, 0, BigDecimal.valueOf(30), 40,
                true, BigDecimal.valueOf(0.95), true, false, 2, "1234",
                "dev-hash", 0, false, false, 100, "1.2", 1, BigDecimal.valueOf(5), false,
                BigDecimal.valueOf(150), BigDecimal.valueOf(180), 0, 2, 6, false, BigDecimal.valueOf(500),
                "bank-hash", BigDecimal.valueOf(0.95), 30, BigDecimal.valueOf(48000), BigDecimal.valueOf(0.9), 0, 1,
                "mobile-hash", 500, false, BigDecimal.valueOf(0.95)
        );

        MlClient.ScoreOutcome outcome = client.score(req);

        assertTrue(outcome.degraded(), "outcome should be marked degraded when ml-service is unreachable");
        assertNull(outcome.response(), "no score response should be returned on failure");
    }
}
