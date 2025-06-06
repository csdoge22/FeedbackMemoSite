package com.sonit.feedbacksite;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AccountController {
    @Autowired
    private AccountRepository accountRepository;

    // Sign up endpoint (Create a new account)
    @PostMapping("/account")
    public Account createAccount(@RequestBody Account account){
        Account savedAccount = accountRepository.save(account);
        return savedAccount;
    }

    // Login endpoint (Authenticate an existing account)
    @PostMapping("/login")
    public Account login(@RequestBody Account account) {
        String username = account.getUsername();
        String password = account.getPassword();

        // Check if the account exists with the given username and password
        return accountRepository.findByUsernameAndPassword(username, password)
                .orElseThrow(() -> new RuntimeException("Invalid username or password"));
    }
}
