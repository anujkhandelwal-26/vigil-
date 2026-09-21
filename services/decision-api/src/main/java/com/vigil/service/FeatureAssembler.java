package com.vigil.service;

import com.vigil.api.dto.ApplicationSubmitRequest;
import com.vigil.repo.ApplicationRepository;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;

/**
 * Computes velocity features server-side from the database, rather than
 * trusting client-supplied values. The submitted request DOES carry
 * device_reuse_count_30d etc. (useful for the demo's scenario prefills),
 * but the number that actually reaches the model is
 * max(client-supplied, server-computed) -- so a real ring building up
 * across several submissions in this running demo is genuinely detected,
 * not just replayed from a canned payload.
 */
@Service
public class FeatureAssembler {

    private final ApplicationRepository applicationRepository;

    public FeatureAssembler(ApplicationRepository applicationRepository) {
        this.applicationRepository = applicationRepository;
    }

    public record Velocity(int deviceReuseCount30d, int ipDistinctApps24h, int accountSharedWithNApplicants) {}

    public Velocity assemble(ApplicationSubmitRequest req) {
        OffsetDateTime now = OffsetDateTime.now();
        long deviceReuse = applicationRepository.countByDeviceHashSince(req.deviceHash(), now.minusDays(30));
        long ipApps = applicationRepository.countByIpPrefixSince(req.ipPrefix(), now.minusHours(24));
        long acctShared = applicationRepository.countByBankAccountHashSince(req.bankAccountHash(), now.minusDays(90));

        int deviceReuseCount30d = (int) Math.max(req.deviceReuseCount30d(), deviceReuse);
        int ipDistinctApps24h = (int) Math.max(req.ipDistinctApps24h(), ipApps);
        int accountShared = (int) Math.max(req.accountSharedWithNApplicants(), acctShared + 1);

        return new Velocity(deviceReuseCount30d, ipDistinctApps24h, accountShared);
    }
}
