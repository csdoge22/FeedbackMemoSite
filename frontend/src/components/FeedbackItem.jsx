/**
 * FeedbackItem
 *
 * Displays a single feedback entry with priority-based styling.
 * Supports both display and edit modes.
 */

import { useState } from "react";

const PRIORITY_STYLES = {
  high: "border-red-500 bg-red-50 text-red-900",
  medium: "border-yellow-500 bg-yellow-50 text-yellow-900",
  low: "border-green-500 bg-green-50 text-green-900",
};

const DEFAULT_STYLE = "border-gray-300 bg-white text-gray-900";
const DEFAULT_PRIORITY = "medium";

export default function FeedbackItem({ feedback, onDelete, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(feedback?.content || "");
  const [editCategory, setEditCategory] = useState(feedback?.category || "");
  const [editPriority, setEditPriority] = useState(feedback?.priority || DEFAULT_PRIORITY);
  const [isSaving, setIsSaving] = useState(false);

  if (!feedback) return null;

  const {
    id,
    content,
    category,
    priority: rawPriority,
  } = feedback;

  const priority = rawPriority ?? DEFAULT_PRIORITY;
  const priorityStyle = PRIORITY_STYLES[priority] ?? DEFAULT_STYLE;

  // Handle save
  async function handleSave() {
    if (!editContent.trim()) {
      alert("Feedback content cannot be empty");
      return;
    }

    setIsSaving(true);
    try {
      await onUpdate(id, {
        content: editContent,
        category: editCategory || null,
        priority: editPriority,
      });
      setIsEditing(false);
    } catch (err) {
      alert(`Failed to update feedback: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  }

  // Handle cancel
  function handleCancel() {
    setEditContent(content);
    setEditCategory(category || "");
    setEditPriority(priority);
    setIsEditing(false);
  }

  // Display mode
  if (!isEditing) {
    return (
      <article
        className={`border rounded-lg p-4 space-y-2 ${priorityStyle}`}
        aria-label={`Feedback item with ${priority} priority`}
      >
        <header className="flex justify-between items-center">
          <span className="text-xs font-medium px-2 py-1 rounded">
            {priority.toUpperCase()}
          </span>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="text-xs text-blue-500 hover:underline"
              aria-label="Edit feedback"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => onDelete(id)}
              className="text-xs text-red-500 hover:underline"
              aria-label="Delete feedback"
            >
              Delete
            </button>
          </div>
        </header>

        <p className="text-sm text-gray-800 whitespace-pre-wrap">
          {content}
        </p>

        {category && (
          <p className="text-xs text-gray-500">
            Category: {category}
          </p>
        )}
      </article>
    );
  }

  // Edit mode
  return (
    <article
      className={`border rounded-lg p-4 space-y-2 ${priorityStyle}`}
      aria-label="Edit feedback item"
    >
      <div className="space-y-3">
        <div>
          <label htmlFor={`content-${id}`} className="block text-xs font-medium mb-1">
            Content
          </label>
          <textarea
            id={`content-${id}`}
            className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            disabled={isSaving}
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label htmlFor={`category-${id}`} className="block text-xs font-medium mb-1">
              Category
            </label>
            <input
              id={`category-${id}`}
              className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
              value={editCategory}
              onChange={(e) => setEditCategory(e.target.value)}
              placeholder="e.g., UI, Performance"
              disabled={isSaving}
            />
          </div>

          <div>
            <label htmlFor={`priority-${id}`} className="block text-xs font-medium mb-1">
              Priority
            </label>
            <select
              id={`priority-${id}`}
              className="w-full border border-gray-300 rounded p-2 focus:outline-none focus:border-blue-500"
              value={editPriority}
              onChange={(e) => setEditPriority(e.target.value)}
              disabled={isSaving}
            >
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={handleCancel}
            className="text-xs px-3 py-1 border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="text-xs px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSaving}
          >
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </article>
  );
}
