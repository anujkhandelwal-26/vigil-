package com.vigil.api.dto;

import jakarta.validation.constraints.*;

import java.math.BigDecimal;

/**
 * Input validation lives here (Jakarta Bean Validation), enforced before a
 * single row reaches the database or the scoring engine -- this is the
 * "input validation" control in the security layer, not a slide.
 */
public record ApplicationSubmitRequest(
        @NotBlank String externalRef,

        @NotNull @Min(18) @Max(100) Integer age,
        @NotBlank String gender,
        @NotBlank String employmentType,
        @NotNull @DecimalMin("0") BigDecimal monthlyIncomeInr,
        @NotNull @Min(1) @Max(3) Integer cityTier,
        @NotBlank @Pattern(regexp = "\\d{3}") String pincodePrefix,
        @NotBlank String residenceType,

        @NotBlank String product,
        @NotNull @DecimalMin("1000") @DecimalMax("5000000") BigDecimal amountInr,
        @NotNull @Min(1) @Max(60) Integer tenureMonths,
        @NotBlank String channel,

        Integer cibilScore,
        @NotNull Boolean isNewToCredit,
        @NotNull @Min(0) Integer activeLoans,
        @NotNull @Min(0) Integer enquiries30d,
        @NotNull @Min(0) Integer maxDpd12m,
        BigDecimal creditUtilisationPct,
        Integer oldestAccountMonths,

        @NotNull Boolean panFormatValid,
        @NotNull @DecimalMin("0") @DecimalMax("1") BigDecimal panNameMatchScore,
        @NotNull Boolean aadhaarPanLinked,
        @NotNull Boolean nameDobMismatch,
        @NotNull @Min(0) Integer digilockerDocsFetched,
        @Pattern(regexp = "\\d{4}") String aadhaarLast4,

        @NotBlank String deviceHash,
        @NotNull @Min(0) Integer deviceReuseCount30d,
        @NotNull Boolean isEmulator,
        @NotNull Boolean isRooted,
        @NotNull @Min(0) Integer appInstallAgeDays,
        @NotBlank String ipPrefix,
        @NotNull @Min(0) Integer ipDistinctApps24h,
        BigDecimal ipPincodeDistanceKm,
        @NotNull Boolean vpnOrProxy,

        @NotNull @DecimalMin("0") BigDecimal formFillSeconds,
        BigDecimal typingSpeedCpm,
        @NotNull @Min(0) Integer pasteEvents,
        @NotNull @Min(0) Integer fieldCorrections,
        @NotNull @Min(0) Integer sessionScreens,
        @NotNull Boolean nightApplication,
        BigDecimal timeSincePrevAppHours,

        @NotBlank String bankAccountHash,
        BigDecimal pennyDropNameMatch,
        Integer accountAgeMonths,
        BigDecimal avgMonthlyCreditInr,
        BigDecimal salaryCreditRegularity,
        @NotNull @Min(0) Integer bounceCount6m,
        @NotNull @Min(1) Integer accountSharedWithNApplicants,

        @NotBlank String mobileHash,
        Integer mobileAgeOnNetworkDays,
        @NotNull Boolean recentSimSwap30d,
        BigDecimal mobileNameMatch
) {}
