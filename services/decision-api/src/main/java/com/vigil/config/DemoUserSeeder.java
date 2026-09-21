package com.vigil.config;

import com.vigil.domain.AppUser;
import com.vigil.repo.AppUserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * Seeds two demo users on first boot: an ANALYST and an ADMIN. The
 * password comes from VIGIL_DEMO_PASSWORD (see .env), generated at
 * bootstrap -- never a hardcoded literal. This exists purely so the
 * recorded demo has something to log in with; a real deployment would
 * remove this seeder entirely.
 */
@Component
public class DemoUserSeeder implements CommandLineRunner {

    private final AppUserRepository repo;
    private final PasswordEncoder encoder;
    private final VigilProperties props;

    public DemoUserSeeder(AppUserRepository repo, PasswordEncoder encoder, VigilProperties props) {
        this.repo = repo;
        this.encoder = encoder;
        this.props = props;
    }

    @Override
    public void run(String... args) {
        String password = props.demo().password();
        if (password == null || password.isBlank()) {
            return; // no demo password configured -- skip seeding, nothing to log in with
        }
        seed("analyst", "Priya Sharma (Analyst)", "ANALYST", password);
        seed("admin", "Risk Ops Admin", "ADMIN", password);
    }

    private void seed(String username, String displayName, String role, String rawPassword) {
        if (repo.findByUsername(username).isPresent()) return;
        AppUser u = new AppUser();
        u.setUsername(username);
        u.setDisplayName(displayName);
        u.setRole(role);
        u.setPasswordHash(encoder.encode(rawPassword));
        repo.save(u);
    }
}
