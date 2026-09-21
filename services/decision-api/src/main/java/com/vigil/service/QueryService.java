package com.vigil.service;

import com.vigil.api.dto.ApplicationSummary;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Read models for the two dashboards -- joins across application/decision
 * that don't map cleanly to a single JPA aggregate, so these go through
 * JdbcTemplate directly rather than forcing an awkward JPQL join.
 */
@Service
public class QueryService {

    private final JdbcTemplate jdbcTemplate;

    public QueryService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<ApplicationSummary> listQueue(String actionFilter, int limit) {
        String sql = """
            SELECT a.id, a.external_ref, a.submitted_at, a.product, a.amount_inr,
                   d.action, d.risk_score, d.latency_ms
            FROM application a
            LEFT JOIN LATERAL (
                SELECT action, risk_score, latency_ms FROM decision
                WHERE application_id = a.id ORDER BY created_at DESC LIMIT 1
            ) d ON true
            WHERE (? = 'ALL' OR d.action = ?)
            ORDER BY a.submitted_at DESC
            LIMIT ?
            """;
        return jdbcTemplate.query(sql, (rs, rowNum) -> new ApplicationSummary(
                UUID.fromString(rs.getString("id")),
                rs.getString("external_ref"),
                rs.getObject("submitted_at", OffsetDateTime.class),
                rs.getString("product"),
                rs.getBigDecimal("amount_inr"),
                rs.getString("action"),
                rs.getBigDecimal("risk_score"),
                (Integer) rs.getObject("latency_ms")
        ), actionFilter, actionFilter, limit);
    }

    public Map<String, Object> kpis() {
        Map<String, Object> out = new LinkedHashMap<>();
        Long totalToday = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM decision WHERE created_at > now() - interval '24 hours'", Long.class);
        out.put("decisionsLast24h", totalToday);

        List<Map<String, Object>> byAction = jdbcTemplate.queryForList(
                "SELECT action, COUNT(*) AS n FROM decision WHERE created_at > now() - interval '24 hours' GROUP BY action");
        out.put("byAction", byAction);

        List<BigDecimal> latencies = jdbcTemplate.queryForList(
                "SELECT latency_ms FROM decision WHERE created_at > now() - interval '24 hours' ORDER BY latency_ms",
                Integer.class).stream().map(BigDecimal::valueOf).toList();
        BigDecimal p95 = latencies.isEmpty() ? BigDecimal.ZERO
                : latencies.get((int) Math.min(latencies.size() - 1, Math.floor(latencies.size() * 0.95)));
        out.put("p95LatencyMs", p95);

        return out;
    }
}
