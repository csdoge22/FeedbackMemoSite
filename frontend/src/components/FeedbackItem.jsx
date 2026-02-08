/**
 * FeedbackItem
 *
 * Displays a single feedback entry with priority-based styling.
 * Stateless and fully controlled by parent.
 */

const PRIORITY_STYLES = {
  high: "border-red-500 bg-red-50 text-red-900",
  medium: "border-yellow-500 bg-yellow-50 text-yellow-900",
  low: "border-green-500 bg-green-50 text-green-900",
};

const DEFAULT_STYLE = "border-gray-300 bg-white text-gray-900";
const DEFAULT_PRIORITY = "medium";

export default function FeedbackItem({ feedback, onDelete }) {
  if (!feedback) return null;

  const {
    id,
    content,
    category,
    priority: rawPriority,
  } = feedback;

  const priority = rawPriority ?? DEFAULT_PRIORITY;
  const priorityStyle = PRIORITY_STYLES[priority] ?? DEFAULT_STYLE;

  return (
    <article
      className={`border rounded-lg p-4 space-y-2 ${priorityStyle}`}
      aria-label={`Feedback item with ${priority} priority`}
    >
      <header className="flex justify-between items-center">
        <span className="text-xs font-medium px-2 py-1 rounded">
          {priority.toUpperCase()}
        </span>

        <button
          type="button"
          onClick={() => onDelete(id)}
          className="text-xs text-red-500 hover:underline"
          aria-label="Delete feedback"
        >
          Delete
        </button>
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
