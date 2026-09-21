export type Role = "admin" | "agent" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export type MessageRole = "user" | "assistant" | "summary";

export interface ChatMessageResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  provider_used: string;
  tokens_used: number;
  matched_category: string | null;
}

export interface MessageOut {
  id: string;
  role: MessageRole;
  content: string;
  tokens_used: number | null;
  provider_used: string | null;
  feedback: boolean | null;
  created_at: string;
}

export type Channel = "chat" | "voice";

export interface ConversationSummary {
  id: string;
  channel: Channel;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  last_message_preview: string | null;
  last_message_at: string | null;
}
