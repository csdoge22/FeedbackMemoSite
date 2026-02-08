import { describe, it, expect } from "vitest";
import userAPI from "../../api/users";

describe("userAPI", () => {
  it("should have register method", () => {
    expect(typeof userAPI.register).toBe("function");
  });

  it("should have login method", () => {
    expect(typeof userAPI.login).toBe("function");
  });

  it("should have logout method", () => {
    expect(typeof userAPI.logout).toBe("function");
  });

  it("should have getCurrentUser method", () => {
    expect(typeof userAPI.getCurrentUser).toBe("function");
  });
});
