package com.vigil.api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

/**
 * Mirrors ml-service's ApplicationIn pydantic schema field-for-field. This
 * record is serialized with a snake_case-configured ObjectMapper (see
 * MlRestClientConfig), so camelCase here maps to snake_case JSON there --
 * the cross-language contract decision-api and ml-service both honour.
 * device_reuse_count_30d / ip_distinct_apps_24h / account_shared_with_n_applicants
 * are the server-computed velocity values (FeatureAssembler), NOT the
 * client-submitted ones.
 */
public record MlScoreRequest(
        String applicationId,
        String externalRef,
        Integer age,
        String gender,
        String employmentType,
        BigDecimal monthlyIncomeInr,
        Integer cityTier,
        String pincodePrefix,
        String residenceType,
        String product,
        BigDecimal amountInr,
        Integer tenureMonths,
        String channel,
        Integer cibilScore,
        Boolean isNewToCredit,
        Integer activeLoans,
        @JsonProperty("enquiries_30d") Integer enquiries30d,
        @JsonProperty("max_dpd_12m") Integer maxDpd12m,
        BigDecimal creditUtilisationPct,
        Integer oldestAccountMonths,
        Boolean panFormatValid,
        BigDecimal panNameMatchScore,
        Boolean aadhaarPanLinked,
        Boolean nameDobMismatch,
        Integer digilockerDocsFetched,
        String aadhaarLast4,
        String deviceHash,
        @JsonProperty("device_reuse_count_30d") Integer deviceReuseCount30d,
        Boolean isEmulator,
        Boolean isRooted,
        Integer appInstallAgeDays,
        String ipPrefix,
        @JsonProperty("ip_distinct_apps_24h") Integer ipDistinctApps24h,
        BigDecimal ipPincodeDistanceKm,
        Boolean vpnOrProxy,
        BigDecimal formFillSeconds,
        BigDecimal typingSpeedCpm,
        Integer pasteEvents,
        Integer fieldCorrections,
        Integer sessionScreens,
        Boolean nightApplication,
        BigDecimal timeSincePrevAppHours,
        String bankAccountHash,
        BigDecimal pennyDropNameMatch,
        Integer accountAgeMonths,
        BigDecimal avgMonthlyCreditInr,
        BigDecimal salaryCreditRegularity,
        @JsonProperty("bounce_count_6m") Integer bounceCount6m,
        @JsonProperty("account_shared_with_n_applicants") Integer accountSharedWithNApplicants,
        String mobileHash,
        Integer mobileAgeOnNetworkDays,
        @JsonProperty("recent_sim_swap_30d") Boolean recentSimSwap30d,
        BigDecimal mobileNameMatch
) {
    public static MlScoreRequest from(String applicationId, ApplicationSubmitRequest r,
                                       int deviceReuseCount30d, int ipDistinctApps24h, int accountSharedWithNApplicants) {
        return new MlScoreRequest(
                applicationId, r.externalRef(), r.age(), r.gender(), r.employmentType(), r.monthlyIncomeInr(),
                r.cityTier(), r.pincodePrefix(), r.residenceType(), r.product(), r.amountInr(), r.tenureMonths(),
                r.channel(), r.cibilScore(), r.isNewToCredit(), r.activeLoans(), r.enquiries30d(), r.maxDpd12m(),
                r.creditUtilisationPct(), r.oldestAccountMonths(), r.panFormatValid(), r.panNameMatchScore(),
                r.aadhaarPanLinked(), r.nameDobMismatch(), r.digilockerDocsFetched(), r.aadhaarLast4(),
                r.deviceHash(), deviceReuseCount30d, r.isEmulator(), r.isRooted(), r.appInstallAgeDays(),
                r.ipPrefix(), ipDistinctApps24h, r.ipPincodeDistanceKm(), r.vpnOrProxy(),
                r.formFillSeconds(), r.typingSpeedCpm(), r.pasteEvents(), r.fieldCorrections(), r.sessionScreens(),
                r.nightApplication(), r.timeSincePrevAppHours(), r.bankAccountHash(), r.pennyDropNameMatch(),
                r.accountAgeMonths(), r.avgMonthlyCreditInr(), r.salaryCreditRegularity(), r.bounceCount6m(),
                accountSharedWithNApplicants, r.mobileHash(), r.mobileAgeOnNetworkDays(), r.recentSimSwap30d(),
                r.mobileNameMatch()
        );
    }
}
