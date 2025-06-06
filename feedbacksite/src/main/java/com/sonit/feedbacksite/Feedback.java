package com.sonit.feedbacksite;

import java.time.LocalDateTime;

import org.hibernate.annotations.OnDelete;
import org.hibernate.annotations.OnDeleteAction;

import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
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
    @Column(nullable = false)
    private String content = "Empty Content";
    @Enumerated(EnumType.STRING)
    private Priority priority;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "subtab_id", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @JsonIgnore
    private SubTab subTab;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Feedback(){
        super();
    }
    public Feedback(int id){
        super();
        this.id = id;
    }

    public SubTab getSubTab() {
        return subTab;
    }
    public String getContent() {
        return content;
    }
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
    public int getId() {
        return id;
    }
    public Priority getPriority() {
        return priority;
    }
    public String getTitle() {
        return title;
    }
    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
    public void setContent(String content) {
        this.content = content;
    }
    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
    public void setId(int id) {
        this.id = id;
    }
    public void setPriority(Priority priority) {
        this.priority = priority;
    }
    public void setSubTab(SubTab subTab) {
        this.subTab = subTab;
    }
    public void setTitle(String title) {
        this.title = title;
    }
    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
