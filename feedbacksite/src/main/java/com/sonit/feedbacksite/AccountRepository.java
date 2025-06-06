package com.sonit.feedbacksite;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountRepository extends JpaRepository<Account, Integer>{
    // Properties of each account
    Optional<Account> findByUsername(String username);
    Optional<Account> findByEmail(String email);
    Optional<Account> findByUsernameAndPassword(String username, String password);
    boolean existsByEmail(String email);
    boolean existsByUsername(String username);
}
