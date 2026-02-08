import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import FeedbackItem from "../../components/FeedbackItem";

describe("FeedbackItem", () => {
  const feedback = {
    id: 42,
    content: "This feature is awesome",
    priority: "high",
    category: "UX",
  };

  it("renders feedback content", () => {
    render(<FeedbackItem feedback={feedback} onDelete={() => {}} />);
    expect(screen.getByText("This feature is awesome")).toBeInTheDocument();
  });

  it("renders priority label in uppercase", () => {
    render(<FeedbackItem feedback={feedback} onDelete={() => {}} />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("renders category when provided", () => {
    render(<FeedbackItem feedback={feedback} onDelete={() => {}} />);
    expect(screen.getByText("Category: UX")).toBeInTheDocument();
  });

  it("does not render category when missing", () => {
    render(
      <FeedbackItem
        feedback={{ ...feedback, category: null }}
        onDelete={() => {}}
      />
    );
    expect(screen.queryByText(/category/i)).not.toBeInTheDocument();
  });

  it("calls onDelete with feedback id", () => {
    const onDelete = vi.fn();
    render(<FeedbackItem feedback={feedback} onDelete={onDelete} />);

    fireEvent.click(screen.getByRole("button", { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith(42);
  });
});
