package com.sonit.feedbacksite;

import java.time.LocalDateTime;

import jakarta.persistence.Entity;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.EnumType;

@Entity
public class Feedback {
    public enum Priority {
        LOW, MEDIUM, HIGH
    }
    @Id
    @GeneratedValue(strategy = jakarta.persistence.GenerationType.IDENTITY)
    private int id;
    private String title;
    private String content;
    @Enumerated(EnumType.STRING)
    private Priority priority;
    private int subTabId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
