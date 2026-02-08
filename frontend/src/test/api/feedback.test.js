import { describe, it, expect } from "vitest";
import feedbackAPI from "../../api/feedback";

describe("feedbackAPI", () => {
  it("should have getMyFeedback method", () => {
    expect(typeof feedbackAPI.getMyFeedback).toBe("function");
  });

  it("should have submitFeedback method", () => {
    expect(typeof feedbackAPI.submitFeedback).toBe("function");
  });

  it("should have updateFeedback method", () => {
    expect(typeof feedbackAPI.updateFeedback).toBe("function");
  });

  it("should have deleteFeedback method", () => {
    expect(typeof feedbackAPI.deleteFeedback).toBe("function");
  });

  it("should have getFeedbackById method", () => {
    expect(typeof feedbackAPI.getFeedbackById).toBe("function");
  });

  it("should have getFeedbackByCategory method", () => {
    expect(typeof feedbackAPI.getFeedbackByCategory).toBe("function");
  });

  it("should have getFeedbackByPriority method", () => {
    expect(typeof feedbackAPI.getFeedbackByPriority).toBe("function");
  });
});
