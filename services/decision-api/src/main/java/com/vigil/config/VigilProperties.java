package com.vigil.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "vigil")
public record VigilProperties(Jwt jwt, MlService mlService, Demo demo) {
    public record Jwt(String secret, int ttlMinutes) {}
    public record MlService(String url, int timeoutMs) {}
    public record Demo(String password) {}
}
