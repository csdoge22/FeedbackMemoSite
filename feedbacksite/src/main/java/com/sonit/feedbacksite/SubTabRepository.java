package com.sonit.feedbacksite;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SubTabRepository extends JpaRepository<SubTab, Integer> {
    List<SubTab> findByTab(Tab tab);
    Optional<SubTab> findByName(String name);
    boolean existsByName(String name);
}