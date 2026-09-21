export interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  providerUsed?: string | null;
  tokensUsed?: number | null;
  feedback?: boolean | null;
  streaming?: boolean;
}
