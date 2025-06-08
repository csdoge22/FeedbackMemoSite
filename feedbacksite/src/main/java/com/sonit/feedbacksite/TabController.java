package com.sonit.feedbacksite;

import java.util.Optional;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class TabController {
    @Autowired
    private TabRepository tabRepository;
    @Autowired
    private AccountRepository accountRepository;

    // Insert a tab for an account by email
    @PostMapping("/tab")
    public ResponseEntity<?> insertTab(@RequestBody Tab tab, @RequestParam("email") String email) {
        if (tabRepository.existsByName(tab.getName())) {
            return ResponseEntity.status(409).body("Tab with this name already exists");
        }
        Optional<Account> accountOpt = accountRepository.findByEmail(email);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Account not found");
        }
        tab.setAccount(accountOpt.get());
        return ResponseEntity.ok(tabRepository.save(tab));
    }

    // List all tabs for an account by email
    @GetMapping("/tabs")
    public ResponseEntity<?> listTabs(@RequestParam("email") String email) {
        Optional<Account> accountOpt = accountRepository.findByEmail(email);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Account not found");
        }
        List<Tab> tabs = tabRepository.findByAccount(accountOpt.get());
        return ResponseEntity.ok(tabs);
    }

    // Get a tab by name
    @GetMapping("/tab")
    public ResponseEntity<?> getTabByName(@RequestParam("name") String name) {
        Optional<Tab> tabOpt = tabRepository.findByName(name);
        if (tabOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Tab not found");
        }
        return ResponseEntity.ok(tabOpt.get());
    }

    // Update the name of a tab by tab id
    @PutMapping("/tab/{id}")
    public ResponseEntity<?> updateTab(@RequestBody Tab updatedTab, @PathVariable("id") Integer id) {
        Optional<Tab> tabOpt = tabRepository.findById(id);
        if (tabOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Tab not found");
        }
        Tab existingTab = tabOpt.get();
        existingTab.setName(updatedTab.getName());
        return ResponseEntity.ok(tabRepository.save(existingTab));
    }

    // Delete a tab by tab id
    @DeleteMapping("/tab/{id}")
    public ResponseEntity<?> deleteTab(@PathVariable("id") Integer id){
        Optional<Tab> tabOpt = tabRepository.findById(id);
        if (tabOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Tab not found");
        }
        tabRepository.delete(tabOpt.get());
        return ResponseEntity.ok("Tab deleted successfully");
    }
}
