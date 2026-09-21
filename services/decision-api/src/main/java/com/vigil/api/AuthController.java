package com.vigil.api;

import com.vigil.api.dto.LoginRequest;
import com.vigil.api.dto.LoginResponse;
import com.vigil.config.JwtService;
import com.vigil.domain.AppUser;
import com.vigil.repo.AppUserRepository;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AppUserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthController(AppUserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest req) {
        AppUser user = userRepository.findByUsername(req.username()).orElse(null);
        // Deliberately uniform error, regardless of which check failed --
        // does not reveal whether the username exists.
        if (user == null || !passwordEncoder.matches(req.password(), user.getPasswordHash())) {
            return ResponseEntity.status(401).build();
        }
        String token = jwtService.issue(user.getUsername(), user.getRole(), user.getId().toString());
        return ResponseEntity.ok(new LoginResponse(token, user.getUsername(), user.getRole(), user.getDisplayName()));
    }
}
