export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type TrustIndicator = {
  key: string;
  level: "info" | "good" | "strong";
};
