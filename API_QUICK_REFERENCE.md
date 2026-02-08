# API Module Quick Reference

## Frontend API Usage Guide

### Feedback API (`src/api/feedback.js`)

All methods automatically include credentials (HTTP-only cookie) with requests.

```javascript
import feedbackAPI from "../api/feedback";

// CREATE - Submit new feedback
const newFeedback = await feedbackAPI.submitFeedback({
  content: "Your feedback here",
  category: "UI",           // optional
  priority: "high",         // optional: "high" | "medium" | "low"
});
// Returns: { id, user_id, content, category, priority }

// READ - Get authenticated user's feedback
const myFeedback = await feedbackAPI.getMyFeedback();
// Returns: [ { id, user_id, content, category, priority }, ... ]

// READ - Get single feedback (public)
const feedback = await feedbackAPI.getFeedbackById(42);
// Returns: { id, user_id, content, category, priority }

// READ - Filter by category (public)
const feedbackByCategory = await feedbackAPI.getFeedbackByCategory("UI");
// Returns: [ { id, ... }, ... ]

// READ - Filter by priority (public)
const feedbackByPriority = await feedbackAPI.getFeedbackByPriority("high");
// Returns: [ { id, ... }, ... ]

// UPDATE - Update feedback (partial update supported)
const updated = await feedbackAPI.updateFeedback(42, {
  content: "Updated content",  // optional
  category: "UX",              // optional
  priority: "medium",          // optional
});
// Returns: { id, user_id, content, category, priority }

// DELETE - Delete feedback
await feedbackAPI.deleteFeedback(42);
// Returns: true
```

### User API (`src/api/users.js`)

All methods automatically include credentials (HTTP-only cookie) with requests.

```javascript
import userAPI from "../api/users";

// REGISTER - Create new user account
const user = await userAPI.register("newuser", "password123");
// Returns: { id, username }

// LOGIN - Authenticate and set cookie
const result = await userAPI.login("username", "password");
// Returns: { message: "Login successful" }
// Side effect: HTTP-only cookie is automatically set by browser

// LOGOUT - Clear authentication cookie
await userAPI.logout();
// Returns: { message: "Logged out successfully" }
// Side effect: HTTP-only cookie is automatically cleared

// GET CURRENT USER - Get authenticated user info
const user = await userAPI.getCurrentUser();
// Returns: { id, username }
// Works with HTTP-only cookie OR Authorization header
```

---

## Component Integration Examples

### In Dashboard/Page Component

```javascript
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import feedbackAPI from "../api/feedback";

export default function MyPage() {
  const { user, loading } = useAuth();
  const [feedback, setFeedback] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) return;  // Don't fetch if not authenticated

    async function loadData() {
      try {
        const data = await feedbackAPI.getMyFeedback();
        setFeedback(data);
      } catch (err) {
        setError(err.message);
      }
    }

    loadData();
  }, [user]);  // Re-fetch when user changes

  if (loading) return <div>Loading auth...</div>;
  if (!user) return <div>Please log in</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {feedback.map(f => (
        <div key={f.id}>{f.content}</div>
      ))}
    </div>
  );
}
```

### In Form Component

```javascript
import { useState } from "react";
import feedbackAPI from "../api/feedback";

export default function FeedbackForm({ onSubmit }) {
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const newFeedback = await feedbackAPI.submitFeedback({
        content,
        category: "General",
        priority: "medium",
      });
      
      onSubmit(newFeedback);
      setContent("");  // Clear form
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        disabled={isSubmitting}
      />
      {error && <div className="error">{error}</div>}
      <button disabled={isSubmitting}>
        {isSubmitting ? "Submitting..." : "Submit"}
      </button>
    </form>
  );
}
```

### With useAuth Hook

```javascript
import { useAuth } from "../context/AuthContext";

export default function UserInfo() {
  const { user, setUser, loading } = useAuth();

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {user ? (
        <div>
          <p>Welcome, {user.username}!</p>
          <button onClick={() => setUser(null)}>Logout</button>
        </div>
      ) : (
        <div>Not logged in</div>
      )}
    </div>
  );
}
```

---

## Error Handling Pattern

All API methods throw Error objects with `message` property:

```javascript
try {
  const feedback = await feedbackAPI.submitFeedback({ content });
} catch (err) {
  // err.message is always a string from the API or network error
  console.error("API Error:", err.message);
  
  // Display to user
  alert(err.message);
  setError(err.message);
}
```

Common error messages:
- "Invalid credentials" - Login failed
- "Not authenticated" - Missing auth token
- "Feedback not found" - Resource doesn't exist or not authorized
- "Failed to submit feedback" - Validation or server error

---

## Authentication Flow

### Login Process
1. User fills login form
2. Call `userAPI.login(username, password)`
3. Backend sets HTTP-only cookie `access_token`
4. Browser automatically saves cookie
5. AuthContext refetches with `userAPI.getCurrentUser()`
6. setUser() updates context → App shows authenticated UI

### Subsequent Requests
1. Component calls `feedbackAPI.getMyFeedback()`
2. fetch() with `credentials: "include"`
3. Browser automatically includes cookie
4. Backend validates JWT from cookie
5. Backend returns user's data

### Logout Process
1. User clicks logout
2. Call `userAPI.logout()`
3. Backend clears cookie
4. Frontend sets `user = null` in AuthContext
5. App shows unauthenticated UI

---

## Common Patterns

### Load Data on Mount
```javascript
useEffect(() => {
  if (!user) return;

  async function loadData() {
    try {
      const data = await feedbackAPI.getMyFeedback();
      setData(data);
    } catch (err) {
      setError(err.message);
    }
  }

  loadData();
}, [user]);
```

### Reload After Action
```javascript
async function handleDelete(id) {
  try {
    await feedbackAPI.deleteFeedback(id);
    // Remove from local state
    setItems(prev => prev.filter(item => item.id !== id));
  } catch (err) {
    setError(err.message);
  }
}
```

### Optimistic Update
```javascript
async function handleUpdate(id, newData) {
  // Update UI immediately
  setItems(prev => prev.map(item => 
    item.id === id ? { ...item, ...newData } : item
  ));

  try {
    // Then update server
    const updated = await feedbackAPI.updateFeedback(id, newData);
    // Sync with server response if needed
    setItems(prev => prev.map(item =>
      item.id === id ? updated : item
    ));
  } catch (err) {
    // Revert on error
    setError(err.message);
    // Could reload data here to resync
  }
}
```

---

## Configuration

### Update API Base URLs
For production, update the `API_BASE` constants:

```javascript
// src/api/feedback.js
const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000/feedback";

// src/api/users.js
const API_BASE = process.env.REACT_APP_AUTH_BASE || "http://localhost:8000/auth";
```

Set in `.env`:
```
REACT_APP_API_BASE=https://api.example.com/feedback
REACT_APP_AUTH_BASE=https://api.example.com/auth
```

---

## Debugging Tips

### Check if User is Authenticated
```javascript
const { user, loading } = useAuth();
console.log("User:", user);
console.log("Loading:", loading);
```

### Check API Requests in Network Tab
1. Open DevTools → Network tab
2. Perform API call
3. Look for requests to `localhost:8000`
4. Check:
   - Request headers include `Cookie: access_token=...`
   - Response status is 200 (success) or expected error code
   - Response body has expected data

### Check Browser Cookies
1. Open DevTools → Application tab
2. Click "Cookies" → "localhost:3000"
3. Should see `access_token` cookie after login
4. Cookie should be `HttpOnly` flag set
5. Cookie should be cleared after logout

### Check Console Errors
```javascript
// Add this to see all API calls
const originalFetch = window.fetch;
window.fetch = function(...args) {
  console.log("API Call:", args);
  return originalFetch.apply(this, args)
    .then(r => (console.log("Response:", r.status), r));
};
```

---

## Testing Checklist

- [ ] Login works and sets cookie
- [ ] User state updates in AuthContext
- [ ] Dashboard loads user's feedback
- [ ] Can add new feedback
- [ ] Can delete feedback
- [ ] Can update feedback
- [ ] Logout clears user state
- [ ] Navigation works when logged in/out
- [ ] Error messages display
- [ ] Loading states show properly
- [ ] No console errors

---

## Support & Troubleshooting

**Problem:** "Not authenticated" error on private endpoints  
**Solution:** Check browser cookies, ensure login was successful, try logout and login again

**Problem:** CORS errors  
**Solution:** Ensure `credentials: "include"` is set and backend has CORS middleware configured

**Problem:** Cookie not persisting  
**Solution:** Check that `secure: False` in development (True in production with HTTPS), check SameSite policy

**Problem:** Getting 404 on /feedback/me  
**Solution:** Ensure backend has the GET /auth/me endpoint, check that user exists in database

---

**Last Updated:** February 7, 2026
