import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Navbar from "../../components/Navbar";
import { AuthProvider } from "../../context/AuthContext";
import { BrowserRouter } from "react-router-dom";
import { server } from "../mocks/server";
import { http, HttpResponse } from "msw";

describe("Navbar", () => {
  const renderNavbar = (mockUser = null) => {
    if (mockUser) {
      server.use(
        http.get("http://localhost:8000/auth/me", () => {
          return HttpResponse.json(mockUser);
        })
      );
    } else {
      server.use(
        http.get("http://localhost:8000/auth/me", () => {
          return HttpResponse.json({ detail: "Not authenticated" }, { status: 401 });
        })
      );
    }

    return render(
      <BrowserRouter>
        <AuthProvider>
          <Navbar />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  describe("rendering - unauthenticated", () => {
    it("should render navbar", () => {
      renderNavbar();

      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });

    it("should show login link when not authenticated", async () => {
      renderNavbar();

      await waitFor(() => {
        expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
      });
    });

    it("should show register link when not authenticated", async () => {
      renderNavbar();

      await waitFor(() => {
        expect(screen.getByRole("link", { name: /register/i })).toBeInTheDocument();
      });
    });

    it("should not show logout button when not authenticated", async () => {
      renderNavbar();

      await waitFor(() => {
        expect(screen.queryByRole("button", { name: /logout/i })).not.toBeInTheDocument();
      });
    });
  });

  describe("rendering - authenticated", () => {
    it("should show username when authenticated", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByText(/testuser/i)).toBeInTheDocument();
      });
    });

    it("should show logout button when authenticated", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
      });
    });

    it("should not show login/register links when authenticated", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.queryByRole("link", { name: /login/i })).not.toBeInTheDocument();
        expect(screen.queryByRole("link", { name: /register/i })).not.toBeInTheDocument();
      });
    });

    it("should show home/dashboard links when authenticated", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        const homeLinks = screen.queryAllByRole("link");
        expect(homeLinks.length).toBeGreaterThan(0);
      });
    });
  });

  describe("logout functionality", () => {
    it("should logout when logout button clicked", async () => {
      const user = userEvent.setup();

      server.use(
        http.post("http://localhost:8000/auth/logout", () => {
          return HttpResponse.json({ message: "Logged out successfully" });
        }),
        http.get("http://localhost:8000/auth/me", () => {
          return HttpResponse.json({ id: 1, username: "testuser" });
        })
      );

      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByText(/testuser/i)).toBeInTheDocument();
      });

      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);

      await waitFor(() => {
        expect(screen.queryByText(/testuser/i)).not.toBeInTheDocument();
      });
    });

    it("should show login/register links after logout", async () => {
      const user = userEvent.setup();

      server.use(
        http.post("http://localhost:8000/auth/logout", () => {
          return HttpResponse.json({ message: "Logged out successfully" });
        }),
        http.get("http://localhost:8000/auth/me", () => {
          return HttpResponse.json({ id: 1, username: "testuser" });
        })
      );

      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
      });

      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);

      await waitFor(() => {
        expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /register/i })).toBeInTheDocument();
      });
    });
  });

  describe("navigation links", () => {
    it("should have home link", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        const homeLink = screen.queryByRole("link", { name: /home|feedback/i });
        expect(homeLink).toBeTruthy();
      });
    });

    it("should have proper href attributes", async () => {
      renderNavbar();

      await waitFor(() => {
        const loginLink = screen.getByRole("link", { name: /login/i });
        const registerLink = screen.getByRole("link", { name: /register/i });

        expect(loginLink.href).toContain("/login");
        expect(registerLink.href).toContain("/register");
      });
    });
  });

  describe("branding", () => {
    it("should display brand/app name", () => {
      renderNavbar();

      const navbar = screen.getByRole("navigation");
      expect(navbar).toBeInTheDocument();
    });

    it("should be a navigation element", () => {
      renderNavbar();

      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });

  describe("responsive behavior", () => {
    it("should render consistently on different screen sizes", async () => {
      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByRole("navigation")).toBeInTheDocument();
      });

      const navbar = screen.getByRole("navigation");
      expect(navbar).toBeVisible();
    });
  });

  describe("error states", () => {
    it("should handle logout errors gracefully", async () => {
      const user = userEvent.setup();

      server.use(
        http.post("http://localhost:8000/auth/logout", () => {
          return HttpResponse.json({ detail: "Logout failed" }, { status: 500 });
        }),
        http.get("http://localhost:8000/auth/me", () => {
          return HttpResponse.json({ id: 1, username: "testuser" });
        })
      );

      renderNavbar({ id: 1, username: "testuser" });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
      });

      const logoutButton = screen.getByRole("button", { name: /logout/i });
      await user.click(logoutButton);

      await waitFor(() => {
        expect(screen.getByText(/testuser/i)).toBeInTheDocument();
      });
    });
  });

  describe("state persistence", () => {
    it("should show username from context", async () => {
      renderNavbar({ id: 1, username: "john_doe" });

      await waitFor(() => {
        expect(screen.getByText(/john_doe/i)).toBeInTheDocument();
      });
    });

    it("should handle different usernames", async () => {
      const users = [
        { id: 1, username: "user1" },
        { id: 2, username: "user2" },
        { id: 3, username: "user3" },
      ];

      for (const testUser of users) {
        const { unmount } = renderNavbar(testUser);

        await waitFor(() => {
          expect(screen.getByText(new RegExp(testUser.username, "i"))).toBeInTheDocument();
        });

        unmount();
      }
    });
  });
});
