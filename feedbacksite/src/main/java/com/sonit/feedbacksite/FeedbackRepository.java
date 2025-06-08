package com.sonit.feedbacksite;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface FeedbackRepository extends JpaRepository<Feedback, Integer> {
    List<Feedback> findBySubTab(SubTab subTab);
    List<Feedback> findByTab(Tab tab);
    List<Feedback> findByPriority(Feedback.Priority priority);
}