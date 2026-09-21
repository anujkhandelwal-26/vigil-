package com.vigil.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;

/**
 * HS256 JWT issuance and verification. The signing secret is read from
 * config (vigil.jwt.secret, sourced from VIGIL_JWT_SECRET) -- never
 * hardcoded, and the app refuses to start with a blank secret (see
 * SecurityConfig).
 */
@Service
public class JwtService {

    private final SecretKey key;
    private final int ttlMinutes;

    public JwtService(VigilProperties props) {
        String secret = props.jwt().secret();
        if (secret == null || secret.isBlank()) {
            throw new IllegalStateException("VIGIL_JWT_SECRET is not set. Refusing to start with no signing key.");
        }
        this.key = Keys.hmacShaKeyFor(secret.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        this.ttlMinutes = props.jwt().ttlMinutes() > 0 ? props.jwt().ttlMinutes() : 60;
    }

    public String issue(String username, String role, String userId) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(username)
                .claim("role", role)
                .claim("uid", userId)
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plus(ttlMinutes, ChronoUnit.MINUTES)))
                .signWith(key)
                .compact();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
    }
}
