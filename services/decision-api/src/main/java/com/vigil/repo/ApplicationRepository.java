package com.vigil.repo;

import com.vigil.domain.Application;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.UUID;

public interface ApplicationRepository extends JpaRepository<Application, UUID> {

    @Query("SELECT COUNT(a) FROM Application a WHERE a.deviceHash = :deviceHash AND a.submittedAt > :since")
    long countByDeviceHashSince(@Param("deviceHash") String deviceHash, @Param("since") java.time.OffsetDateTime since);

    @Query("SELECT COUNT(a) FROM Application a WHERE a.ipPrefix = :ipPrefix AND a.submittedAt > :since")
    long countByIpPrefixSince(@Param("ipPrefix") String ipPrefix, @Param("since") java.time.OffsetDateTime since);

    @Query("SELECT COUNT(a) FROM Application a WHERE a.bankAccountHash = :bankAccountHash AND a.submittedAt > :since")
    long countByBankAccountHashSince(@Param("bankAccountHash") String bankAccountHash, @Param("since") java.time.OffsetDateTime since);

    @Query("SELECT COUNT(a) FROM Application a WHERE a.mobileHash = :mobileHash AND a.submittedAt > :since")
    long countByMobileHashSince(@Param("mobileHash") String mobileHash, @Param("since") java.time.OffsetDateTime since);
}
