/**
 * Centralized User/Auth API Module
 * 
 * Handles authentication-related API calls:
 * - User registration
 * - User login (with HTTP-only cookie)
 * - User logout
 * - Get current user info
 * 
 * Works with backend /auth and /user endpoints
 */

const API_BASE = "http://localhost:8000/auth"; // Adjust if backend runs on different port

/**
 * Error handler: Extract meaningful error messages from API responses
 */
async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }
  return await response.json();
}

/**
 * Common fetch options for authenticated requests
 * Includes credentials to send HTTP-only cookie with each request
 */
const authenticatedOptions = {
  credentials: "include", // Include HTTP-only cookies
  headers: {
    "Content-Type": "application/json",
  },
};

// =====================================================================
// AUTHENTICATION OPERATIONS
// =====================================================================

/**
 * Register a new user
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Object} User object with id, username
 */
async function register(username, password) {
  const response = await fetch(`${API_BASE}/register`, {
    method: "POST",
    ...authenticatedOptions,
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(response);
}

/**
 * Login user and set HTTP-only authentication cookie
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Object} { access_token, user: { id, username } }
 */
async function login(username, password) {
  const response = await fetch(`${API_BASE}/login`, {
    method: "POST",
    ...authenticatedOptions,
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(response);
}

/**
 * Logout user and clear HTTP-only authentication cookie
 * @returns {Object} Success message
 */
async function logout() {
  const response = await fetch(`${API_BASE}/logout`, {
    method: "POST",
    ...authenticatedOptions,
  });
  return handleResponse(response);
}

/**
 * Get current authenticated user info
 * Works with both HTTP-only cookie and Authorization header
 * @returns {Object} User object with id, username
 */
async function getCurrentUser() {
  const response = await fetch(`${API_BASE}/me`, {
    method: "GET",
    ...authenticatedOptions,
  });
  return handleResponse(response);
}

// =====================================================================
// EXPORT API
// =====================================================================

const userAPI = {
  register,
  login,
  logout,
  getCurrentUser,
};

export default userAPI;
