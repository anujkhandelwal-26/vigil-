package com.vigil.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "model_registry")
@Getter
@Setter
@NoArgsConstructor
public class ModelRegistry {

    @Id
    @GeneratedValue
    @Column(name = "id")
    private UUID id;

    @Column(name = "version", nullable = false, unique = true)
    private String version;

    @Column(name = "algorithm", nullable = false)
    private String algorithm;

    @Column(name = "trained_at", nullable = false)
    private OffsetDateTime trainedAt;

    @Column(name = "training_rows") private Integer trainingRows;
    @Column(name = "feedback_rows_used") private Integer feedbackRowsUsed;
    @Column(name = "pr_auc") private BigDecimal prAuc;
    @Column(name = "recall_at_1pct_fpr") private BigDecimal recallAt1pctFpr;
    @Column(name = "fp_rate") private BigDecimal fpRate;
    @Column(name = "threshold_low") private BigDecimal thresholdLow;
    @Column(name = "threshold_high") private BigDecimal thresholdHigh;
    @Column(name = "threshold_decline") private BigDecimal thresholdDecline;

    @Column(name = "active", nullable = false)
    private Boolean active = false;

    @Column(name = "promoted_reason")
    private String promotedReason;
}
