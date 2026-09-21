package com.vigil.service;

import com.vigil.api.dto.ApplicationSubmitRequest;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * ~15 deterministic, explainable rules -- a safety net that runs in-memory
 * BEFORE the ML call, independent of it. A rule can only ESCALATE the
 * final action (never downgrade one the model raised), and each rule that
 * fires contributes its own reason code. This is what keeps the system
 * safe even in the ML_UNAVAILABLE_RULES_ONLY degraded path.
 */
@Service
public class RuleEngine {

    private static final Map<String, Integer> SEVERITY = Map.of(
            "APPROVE", 0, "STEP_UP", 1, "REVIEW", 2, "DECLINE", 3);

    public record RuleResult(String action, List<String> reasonCodes) {}

    public RuleResult evaluate(ApplicationSubmitRequest req, int deviceReuseCount30d, int ipDistinctApps24h, int accountSharedWithNApplicants) {
        String action = "APPROVE";
        List<String> reasons = new ArrayList<>();

        if (Boolean.TRUE.equals(req.isEmulator()) || Boolean.TRUE.equals(req.isRooted())) {
            action = escalate(action, "REVIEW");
            reasons.add("EMULATOR_OR_ROOTED");
        }
        if (deviceReuseCount30d >= 8) {
            action = escalate(action, "DECLINE");
            reasons.add("DEVICE_REUSE_HIGH");
        } else if (deviceReuseCount30d >= 3) {
            action = escalate(action, "REVIEW");
            reasons.add("DEVICE_REUSE_HIGH");
        }
        if (ipDistinctApps24h >= 5) {
            action = escalate(action, "REVIEW");
            reasons.add("IP_MULTI_APPLICANT");
        }
        if (req.enquiries30d() != null && req.enquiries30d() >= 6) {
            action = escalate(action, "STEP_UP");
            reasons.add("BUREAU_ENQUIRY_BURST");
        }
        if (Boolean.FALSE.equals(req.panFormatValid())) {
            action = escalate(action, "DECLINE");
            reasons.add("PAN_NAME_MISMATCH");
        }
        if (req.panNameMatchScore() != null && req.panNameMatchScore().compareTo(BigDecimal.valueOf(0.5)) < 0) {
            action = escalate(action, "REVIEW");
            reasons.add("PAN_NAME_MISMATCH");
        }
        if (Boolean.FALSE.equals(req.aadhaarPanLinked())) {
            action = escalate(action, "STEP_UP");
            reasons.add("AADHAAR_PAN_NOT_LINKED");
        }
        if (accountSharedWithNApplicants >= 4) {
            action = escalate(action, "DECLINE");
            reasons.add("BANK_ACCOUNT_SHARED");
        }
        if (Boolean.TRUE.equals(req.recentSimSwap30d())) {
            action = escalate(action, "STEP_UP");
            reasons.add("SIM_SWAP_RECENT");
        }
        if (req.formFillSeconds() != null && req.formFillSeconds().compareTo(BigDecimal.valueOf(20)) < 0
                && req.pasteEvents() != null && req.pasteEvents() >= 2) {
            action = escalate(action, "REVIEW");
            reasons.add("BEHAVIOUR_FAST_FORM_FILL");
        }
        if (req.amountInr() != null && req.amountInr().compareTo(BigDecimal.valueOf(200000)) > 0
                && Boolean.TRUE.equals(req.isNewToCredit())) {
            action = escalate(action, "STEP_UP");
            reasons.add("THIN_OR_NO_BUREAU_FILE");
        }

        return new RuleResult(action, reasons);
    }

    private String escalate(String current, String candidate) {
        return SEVERITY.get(candidate) > SEVERITY.get(current) ? candidate : current;
    }

    public static String maxSeverity(String a, String b) {
        return SEVERITY.get(a) >= SEVERITY.get(b) ? a : b;
    }
}
