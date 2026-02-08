import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("http://localhost:8000/auth/me", () => {
    return HttpResponse.json({
      id: 1,
      username: "sonit",
    });
  }),
];
