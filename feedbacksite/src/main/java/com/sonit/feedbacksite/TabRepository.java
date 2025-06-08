package com.sonit.feedbacksite;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface TabRepository extends JpaRepository<Tab, Integer> {
    List<Tab> findByAccount(Account account);
    Optional<Tab> findByName(String name);
    boolean existsByName(String name);
}