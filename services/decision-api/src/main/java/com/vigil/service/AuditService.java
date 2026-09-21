package com.vigil.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/**
 * Every decision, override and retrain is written here with actor and
 * timestamp -- the audit trail backing "secure API usage" / "responsible
 * data handling". Kept as a raw JdbcTemplate insert (not a JPA entity)
 * since audit_log.payload is a free-form JSONB blob, not a fixed shape.
 */
@Service
public class AuditService {

    private final JdbcTemplate jdbcTemplate;

    public AuditService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public void log(String actor, String action, String entity, String entityId, String note) {
        String payload = "{\"note\": " + quoteJson(note) + "}";
        jdbcTemplate.update(
                "INSERT INTO audit_log (actor, action, entity, entity_id, payload) VALUES (?, ?, ?, ?, ?::jsonb)",
                actor, action, entity, entityId, payload);
    }

    private String quoteJson(String s) {
        if (s == null) return "null";
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
}
