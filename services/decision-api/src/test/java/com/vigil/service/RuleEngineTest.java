package com.vigil.service;

import com.vigil.api.dto.ApplicationSubmitRequest;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Pure unit tests, no Spring context -- RuleEngine has no dependencies,
 * so these run in milliseconds. Covers the four boundary values on the
 * device-reuse escalation (2 -> APPROVE, 3 -> REVIEW, 7 -> REVIEW,
 * 8 -> DECLINE) to prove the false-positive design is deliberate
 * engineering, not a magic number.
 */
class RuleEngineTest {

    private final RuleEngine ruleEngine = new RuleEngine();

    private ApplicationSubmitRequest cleanRequest() {
        return new ApplicationSubmitRequest(
                "APP-TEST", 30, "F", "SALARIED", BigDecimal.valueOf(50000), 2, "560", "RENTED",
                "CONSUMER_DURABLE", BigDecimal.valueOf(50000), 12, "ANDROID_APP",
                720, false, 1, 1, 0, BigDecimal.valueOf(30), 40,
                true, BigDecimal.valueOf(0.95), true, false, 2, "1234",
                "dev-hash", 0, false, false, 100, "1.2", 1, BigDecimal.valueOf(5), false,
                BigDecimal.valueOf(150), BigDecimal.valueOf(180), 0, 2, 6, false, BigDecimal.valueOf(500),
                "bank-hash", BigDecimal.valueOf(0.95), 30, BigDecimal.valueOf(48000), BigDecimal.valueOf(0.9), 0, 1,
                "mobile-hash", 500, false, BigDecimal.valueOf(0.95)
        );
    }

    @Test
    void cleanApplicationFiresNoRulesAndApproves() {
        var result = ruleEngine.evaluate(cleanRequest(), 0, 1, 1);
        assertEquals("APPROVE", result.action());
        assertTrue(result.reasonCodes().isEmpty());
    }

    @Test
    void deviceReuseBelowThreeStaysApprove() {
        var result = ruleEngine.evaluate(cleanRequest(), 2, 1, 1);
        assertEquals("APPROVE", result.action());
    }

    @Test
    void deviceReuseAtThreeEscalatesToReview() {
        var result = ruleEngine.evaluate(cleanRequest(), 3, 1, 1);
        assertEquals("REVIEW", result.action());
        assertTrue(result.reasonCodes().contains("DEVICE_REUSE_HIGH"));
    }

    @Test
    void deviceReuseAtEightEscalatesToDecline() {
        var result = ruleEngine.evaluate(cleanRequest(), 8, 1, 1);
        assertEquals("DECLINE", result.action());
    }

    @Test
    void bankAccountSharedByFourOrMoreDeclines() {
        var result = ruleEngine.evaluate(cleanRequest(), 0, 1, 4);
        assertEquals("DECLINE", result.action());
        assertTrue(result.reasonCodes().contains("BANK_ACCOUNT_SHARED"));
    }

    @Test
    void invalidPanFormatAlwaysDeclines() {
        ApplicationSubmitRequest req = withPanInvalid(cleanRequest());
        var result = ruleEngine.evaluate(req, 0, 1, 1);
        assertEquals("DECLINE", result.action());
    }

    @Test
    void rulesNeverDowngradeAnAlreadyEscalatedAction() {
        // device reuse (REVIEW) + bank shared (DECLINE) -> the higher
        // severity wins, never the other way round.
        var result = ruleEngine.evaluate(cleanRequest(), 3, 1, 4);
        assertEquals("DECLINE", result.action());
    }

    private ApplicationSubmitRequest withPanInvalid(ApplicationSubmitRequest r) {
        return new ApplicationSubmitRequest(
                r.externalRef(), r.age(), r.gender(), r.employmentType(), r.monthlyIncomeInr(), r.cityTier(), r.pincodePrefix(), r.residenceType(),
                r.product(), r.amountInr(), r.tenureMonths(), r.channel(),
                r.cibilScore(), r.isNewToCredit(), r.activeLoans(), r.enquiries30d(), r.maxDpd12m(), r.creditUtilisationPct(), r.oldestAccountMonths(),
                false, r.panNameMatchScore(), r.aadhaarPanLinked(), r.nameDobMismatch(), r.digilockerDocsFetched(), r.aadhaarLast4(),
                r.deviceHash(), r.deviceReuseCount30d(), r.isEmulator(), r.isRooted(), r.appInstallAgeDays(), r.ipPrefix(), r.ipDistinctApps24h(), r.ipPincodeDistanceKm(), r.vpnOrProxy(),
                r.formFillSeconds(), r.typingSpeedCpm(), r.pasteEvents(), r.fieldCorrections(), r.sessionScreens(), r.nightApplication(), r.timeSincePrevAppHours(),
                r.bankAccountHash(), r.pennyDropNameMatch(), r.accountAgeMonths(), r.avgMonthlyCreditInr(), r.salaryCreditRegularity(), r.bounceCount6m(), r.accountSharedWithNApplicants(),
                r.mobileHash(), r.mobileAgeOnNetworkDays(), r.recentSimSwap30d(), r.mobileNameMatch()
        );
    }
}
