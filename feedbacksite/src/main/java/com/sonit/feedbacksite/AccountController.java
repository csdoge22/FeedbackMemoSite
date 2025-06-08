package com.sonit.feedbacksite;

import java.time.LocalDateTime;
import java.util.Optional;

import org.apache.catalina.connector.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
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
    public ResponseEntity<?> createAccount(@RequestBody Account account){
        if (accountRepository.existsByEmail(account.getEmail())) {
            return ResponseEntity.status(409).body("Account with this email already exists");
        }
        // Username is required and cannot be empty
        if (account.getUsername() == null || account.getUsername().isEmpty()) {
            return ResponseEntity.status(400).body("Username cannot be empty");
        }
        // check if password has at least 8 characters
        if (account.getPassword() == null || account.getPassword().length() < 8) {
            return ResponseEntity.status(400).body("Password must be at least 8 characters long");
        }

        int numSpecialChars = 0;
        int numDigits = 0;
        int numUpperCase = 0;
        int numLowerCase = 0;
        for(int i=0; i<account.getPassword().length(); i++){
            char c = account.getPassword().charAt(i);
            if (Character.isDigit(c)) {
                numDigits++;
            } else if (Character.isUpperCase(c)) {
                numUpperCase++;
            } else if (Character.isLowerCase(c)) {
                numLowerCase++;
            } else if (!Character.isLetterOrDigit(c)) {
                numSpecialChars++;
            }
        }
        if (numSpecialChars < 1 || numDigits < 1 || numUpperCase < 1 || numLowerCase < 1) {
            return ResponseEntity.status(400).body("Password must contain at least one digit, one uppercase letter, one lowercase letter, and one special character");
        }

        // Hash the valid password before saving
        account.setPassword(passwordEncoder.encode(account.getPassword()));
        account.setCreatedAt(LocalDateTime.now());
        return ResponseEntity.ok(accountRepository.save(account));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Account account) {
        String username = account.getUsername();
        String rawPassword = account.getPassword();

        Optional<Account> dbAccountOpt = accountRepository.findByUsername(username);
        if(dbAccountOpt.isEmpty()) {
            return ResponseEntity.status(401).body("Account does not exist");
        }

        Account dbAccount = dbAccountOpt.get();
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

    // retrieve account information
    @GetMapping("/account/me")
    public ResponseEntity<?> retrieveAccount(@PathVariable int id) {
        // Check if the account exists
        Optional<Account> accountOpt = accountRepository.findById(id);
        if(accountOpt.isEmpty()){
            return ResponseEntity.notFound().build();
        } else {
            Account account = accountOpt.get();
            return ResponseEntity.ok(account);
        }
    }

    @PutMapping("/account/update/{id}")
    public ResponseEntity<?> updateAccount(@PathVariable int id, @RequestBody Account updatedAccount) {
        // Check if the account exists
        Optional<Account> accountOpt = accountRepository.findById(id);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Account existingAccount = accountOpt.get();

        // Update fields
        if (updatedAccount.getUsername() != null) {
            existingAccount.setUsername(updatedAccount.getUsername());
        }
        if (updatedAccount.getEmail() != null) {
            existingAccount.setEmail(updatedAccount.getEmail());
        }
        if (updatedAccount.getPassword() != null) {
            String newPassword = updatedAccount.getPassword();
            // Password validation
            if (newPassword.length() < 8) {
                return ResponseEntity.status(400).body("Password must be at least 8 characters long");
            }
            int numSpecialChars = 0;
            int numDigits = 0;
            int numUpperCase = 0;
            int numLowerCase = 0;
            for (int i = 0; i < newPassword.length(); i++) {
                char c = newPassword.charAt(i);
                if (Character.isDigit(c)) {
                    numDigits++;
                } else if (Character.isUpperCase(c)) {
                    numUpperCase++;
                } else if (Character.isLowerCase(c)) {
                    numLowerCase++;
                } else if (!Character.isLetterOrDigit(c)) {
                    numSpecialChars++;
                }
            }
            if (numSpecialChars < 1 || numDigits < 1 || numUpperCase < 1 || numLowerCase < 1) {
                return ResponseEntity.status(400).body("Password must contain at least one digit, one uppercase letter, one lowercase letter, and one special character");
            }
            existingAccount.setPassword(passwordEncoder.encode(newPassword));
        }

        // Save the updated account
        existingAccount.setCreatedAt(LocalDateTime.now());
        return ResponseEntity.ok(accountRepository.save(existingAccount));
    }
}
