package com.vigil;

import com.vigil.config.VigilProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(VigilProperties.class)
public class VigilApplication {
    public static void main(String[] args) {
        SpringApplication.run(VigilApplication.class, args);
    }
}
