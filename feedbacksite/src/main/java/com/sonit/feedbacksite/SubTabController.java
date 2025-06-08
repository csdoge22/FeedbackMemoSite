package com.sonit.feedbacksite;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class SubTabController {
    @Autowired
    private SubTabRepository subTabRepository;
    @Autowired
    private TabRepository tabRepository;
    @Autowired
    private AccountRepository accountRepository;

    // Insert a sub-tab for a given tab (by tab name and account email)
    @PostMapping("/subtab")
    public ResponseEntity<?> insertSubTab(
            @RequestBody SubTab subtab,
            @RequestParam("tabName") String tabName,
            @RequestParam("email") String email) {
        if (subTabRepository.existsByName(subtab.getName())) {
            return ResponseEntity.status(409).body("Sub-tab with this name already exists");
        }
        Optional<Account> accountOpt = accountRepository.findByEmail(email);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Account not found");
        }
        Optional<Tab> tabOpt = tabRepository.findByName(tabName);
        if (tabOpt.isEmpty() || !tabOpt.get().getAccount().getEmail().equals(email)) {
            return ResponseEntity.status(404).body("Tab not found for this account");
        }
        subtab.setTab(tabOpt.get());
        return ResponseEntity.ok(subTabRepository.save(subtab));
    }

    // List all subtabs for a given tab (by tab name and account email)
    @GetMapping("/subtabs")
    public ResponseEntity<?> listSubTabs(
            @RequestParam("tabName") String tabName,
            @RequestParam("email") String email) {
        Optional<Account> accountOpt = accountRepository.findByEmail(email);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Account not found");
        }
        Optional<Tab> tabOpt = tabRepository.findByName(tabName);
        if (tabOpt.isEmpty() || !tabOpt.get().getAccount().getEmail().equals(email)) {
            return ResponseEntity.status(404).body("Tab not found for this account");
        }
        List<SubTab> subtabs = subTabRepository.findByTab(tabOpt.get());
        return ResponseEntity.ok(subtabs);
    }

    // Get a subtab by name (for a given tab and account)
    @GetMapping("/subtab")
    public ResponseEntity<?> getSubTabByName(
            @RequestParam("subtabName") String subtabName,
            @RequestParam("tabName") String tabName,
            @RequestParam("email") String email) {
        Optional<Account> accountOpt = accountRepository.findByEmail(email);
        if (accountOpt.isEmpty()) {
            return ResponseEntity.status(404).body("Account not found");
        }
        Optional<Tab> tabOpt = tabRepository.findByName(tabName);
        if (tabOpt.isEmpty() || !tabOpt.get().getAccount().getEmail().equals(email)) {
            return ResponseEntity.status(404).body("Tab not found for this account");
        }
        Optional<SubTab> subTabOpt = subTabRepository.findByName(subtabName);
        if (subTabOpt.isEmpty() || !subTabOpt.get().getTab().getName().equals(tabName)) {
            return ResponseEntity.status(404).body("SubTab not found for this tab");
        }
        return ResponseEntity.ok(subTabOpt.get());
    }

    // Update a subtab's name by subtab id
    @PutMapping("/subtab/{id}")
    public ResponseEntity<?> updateSubTab(@RequestBody SubTab updatedSubTab, @PathVariable("id") Integer id) {
        Optional<SubTab> subTabOpt = subTabRepository.findById(id);
        if (subTabOpt.isEmpty()) {
            return ResponseEntity.status(404).body("SubTab not found");
        }
        SubTab existingSubTab = subTabOpt.get();
        existingSubTab.setName(updatedSubTab.getName());
        return ResponseEntity.ok(subTabRepository.save(existingSubTab));
    }

    // Delete a subtab by id
    @DeleteMapping("/subtab/{id}")
    public ResponseEntity<?> deleteSubTab(@PathVariable("id") Integer id) {
        Optional<SubTab> subTabOpt = subTabRepository.findById(id);
        if (subTabOpt.isEmpty()) {
            return ResponseEntity.status(404).body("SubTab not found");
        }
        subTabRepository.delete(subTabOpt.get());
        return ResponseEntity.ok("SubTab deleted successfully");
    }
}
