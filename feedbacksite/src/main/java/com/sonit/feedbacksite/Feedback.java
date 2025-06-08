package com.sonit.feedbacksite;

import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.Target;
import java.lang.annotation.ElementType;
import java.lang.annotation.RetentionPolicy;
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
import jakarta.validation.Constraint;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import jakarta.validation.Payload;
import jakarta.persistence.EnumType;

@Documented
@Constraint(validatedBy = AtLeastOnePresentValidator.class)
@Target({ ElementType.TYPE })
@Retention(RetentionPolicy.RUNTIME)
@interface AtLeastOnePresent {
    String message() default "Either subTab or tab must be present";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
class AtLeastOnePresentValidator implements ConstraintValidator<AtLeastOnePresent, Feedback> {
    @Override
    public boolean isValid(Feedback feedback, ConstraintValidatorContext context) {
        return feedback.getSubTab() != null || feedback.getTab() != null;
    }
}
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

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "tab_id", nullable = false)
    @OnDelete(action = OnDeleteAction.CASCADE)
    @JsonIgnore
    private Tab tab;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public Feedback(){
        super();
    }
    public Feedback(int id){
        super();
        this.id = id;
    }
    public Tab getTab() {
        return tab;
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
    public void setTab(Tab tab) {
        this.tab = tab;
    }
}
