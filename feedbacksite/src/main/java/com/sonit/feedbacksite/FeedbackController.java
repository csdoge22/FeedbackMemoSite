package com.sonit.feedbacksite;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class FeedbackController {
    @Autowired
    private FeedbackRepository feedbackRepository;
    @Autowired
    private SubTabRepository subTabRepository;
    @Autowired
    private TabRepository tabRepository;

    // Create feedback for a subtab
    @PostMapping("/feedback")
    public ResponseEntity<?> createFeedback(
            @RequestBody Feedback feedback,
            @RequestParam(value = "subTabId", required = false) Integer subTabId,
            @RequestParam(value = "tabId", required = false) Integer tabId) {
        if (subTabId == null && tabId == null) {
            return ResponseEntity.badRequest().body("Either subTabId or tabId must be provided");
        }
        if (subTabId != null) {
            Optional<SubTab> subTabOpt = subTabRepository.findById(subTabId);
            if (subTabOpt.isEmpty()) {
                return ResponseEntity.status(404).body("SubTab not found");
            }
            feedback.setSubTab(subTabOpt.get());
        }
        if (tabId != null) {
            Optional<Tab> tabOpt = tabRepository.findById(tabId);
            if (tabOpt.isEmpty()) {
                return ResponseEntity.status(404).body("Tab not found");
            }
            feedback.setTab(tabOpt.get());
        }
        feedback.setCreatedAt(java.time.LocalDateTime.now());
        return ResponseEntity.ok(feedbackRepository.save(feedback));
    }

    // List feedback for a subtab
    @GetMapping("/feedbacks")
    public ResponseEntity<?> listFeedbacks(
            @RequestParam(value = "subTabId", required = false) Integer subTabId,
            @RequestParam(value = "tabId", required = false) Integer tabId) {
        if (subTabId != null) {
            Optional<SubTab> subTabOpt = subTabRepository.findById(subTabId);
            if (subTabOpt.isEmpty()) {
                return ResponseEntity.status(404).body("SubTab not found");
            }
            List<Feedback> feedbacks = feedbackRepository.findBySubTab(subTabOpt.get());
            return ResponseEntity.ok(feedbacks);
        } else if (tabId != null) {
            Optional<Tab> tabOpt = tabRepository.findById(tabId);
            if (tabOpt.isEmpty()) {
                return ResponseEntity.status(404).body("Tab not found");
            }
            List<Feedback> feedbacks = feedbackRepository.findByTab(tabOpt.get());
            return ResponseEntity.ok(feedbacks);
        } else {
            return ResponseEntity.badRequest().body("Either subTabId or tabId must be provided");
        }
    }

    // Get feedback by id
    @GetMapping("/feedback/{id}")
    public ResponseEntity<?> getFeedback(@PathVariable("id") Integer id) {
        Optional<Feedback> feedbackOpt = feedbackRepository.findById(id);
        if (feedbackOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Feedback not found");
        }
        return ResponseEntity.ok(feedbackOpt.get());
    }

    // Update feedback by id
    @PutMapping("/feedback/{id}")
    public ResponseEntity<?> updateFeedback(@PathVariable("id") Integer id, @RequestBody Feedback updatedFeedback) {
        Optional<Feedback> feedbackOpt = feedbackRepository.findById(id);
        if (feedbackOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Feedback not found");
        }
        Feedback feedback = feedbackOpt.get();
        feedback.setTitle(updatedFeedback.getTitle());
        feedback.setContent(updatedFeedback.getContent());
        feedback.setPriority(updatedFeedback.getPriority());
        feedback.setUpdatedAt(java.time.LocalDateTime.now());
        return ResponseEntity.ok(feedbackRepository.save(feedback));
    }

    // Delete feedback by id
    @DeleteMapping("/feedback/{id}")
    public ResponseEntity<?> deleteFeedback(@PathVariable("id") Integer id) {
        Optional<Feedback> feedbackOpt = feedbackRepository.findById(id);
        if (feedbackOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Feedback not found");
        }
        feedbackRepository.delete(feedbackOpt.get());
        return ResponseEntity.ok("Feedback deleted successfully");
    }
}
