package com.sonit.feedbacksite;

import java.time.LocalDateTime;

import org.apache.catalina.connector.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.context.annotation.Bean;

@RestController
public class AccountController {
    @Autowired
    private AccountRepository accountRepository;
    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @PostMapping("/account")
    public Account createAccount(@RequestBody Account account){
        account.setPassword(passwordEncoder.encode(account.getPassword()));
        account.setCreatedAt(LocalDateTime.now());
        return accountRepository.save(account);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Account account) {
        String username = account.getUsername();
        String rawPassword = account.getPassword();

        Account dbAccount = accountRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("Invalid username or password"));

        if (!passwordEncoder.matches(rawPassword, dbAccount.getPassword())) {
            return ResponseEntity.status(401).body("Invalid username or password");
        }

        return ResponseEntity.ok(dbAccount);
    }

    @PostMapping("/logout")
    public ResponseEntity<?> logout(){
        return ResponseEntity.ok("Logged out successfully");
    }

    @DeleteMapping("/account/{id}")
    public ResponseEntity<?> deleteAccount(@PathVariable int id, @RequestBody Account account) {
        // Check if the account exists
        if (!accountRepository.existsById(id)) {
            return ResponseEntity.notFound().build();
        }

        // Delete the account
        accountRepository.deleteById(id);
        return ResponseEntity.ok().build();
    }
}
