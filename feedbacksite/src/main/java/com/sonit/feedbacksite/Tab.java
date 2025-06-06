package com.sonit.feedbacksite;

import java.time.LocalDateTime;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

@Entity
public class Tab {
    @Id
    @GeneratedValue(strategy = jakarta.persistence.GenerationType.IDENTITY)
    private int id;
    private String name;
    private int user_id;
    private LocalDateTime createdAt;

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    public String getName() {
        return name;
    }
    public int getUserId() {
        return user_id;
    }
    public int getId() {
        return id;
    }
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    public void setName(String name) {
        this.name = name;
    }
    public void setUserId(int user_id) {
        this.user_id = user_id;
    }
    public void setId(int id) {
        this.id = id;
    }
}
