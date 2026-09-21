import { ApiError } from "./api";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "rate_limited") return "Too many attempts. Please wait a moment and try again.";
    return error.message;
  }
  return "Something went wrong. Please try again.";
}
