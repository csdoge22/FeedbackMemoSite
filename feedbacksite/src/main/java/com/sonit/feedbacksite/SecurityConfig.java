package com.sonit.feedbacksite;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

// This configuration class sets up security for the application, allowing access to Swagger UI and API documentation without logging in.
@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth.requestMatchers(
                    // Swagger/OpenAPI
                    "/swagger-ui/**",
                    "/swagger-ui.html",
                    "/v3/api-docs/**",
                    "/v3/api-docs.yaml",
                    // AccountController
                    "/account",
                    "/account/**",
                    "/login",
                    "/logout",
                    // TabController
                    "/tab",
                    "/tab/**",
                    "/tabs",
                    // SubTabController
                    "/subtab",
                    "/subtab/**",
                    "/subtabs",
                    // FeedbackController
                    "/feedback",
                    "/feedback/**",
                    "/feedbacks"
        ).permitAll().anyRequest().authenticated()
        )
            .csrf(csrf -> csrf.disable())
            .httpBasic(); // or .httpBasic() if you prefer

        return http.build();
    }
}
