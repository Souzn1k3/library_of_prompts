export type AnalyticsEventName =
  | "signup_completed"
  | "first_visit"
  | "page_viewed"
  | "onboarding_started"
  | "onboarding_completed"
  | "onboarding_first_action"
  | "prompt_viewed"
  | "prompt_copied"
  | "prompt_saved"
  | "mission_started"
  | "mission_progressed"
  | "mission_completed"
  | "mission_next_step_clicked"
  | "submission_form_submitted"
  | "submission_created"
  | "submission_moderated"
  | "submission_engaged"
  | "locked_content_viewed"
  | "upgrade_clicked"
  | "checkout_started"
  | "subscription_activated"
  | "catalog_search_used"
  | "catalog_filter_used";

export type Attribution = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  referrer?: string;
};

export type AnalyticsPayloadEvent = {
  event_id: string;
  event_name: AnalyticsEventName;
  session_id: string;
  timestamp: string;
  source: "web";
  context: {
    page: string;
    feature: string;
  };
  attribution: Attribution;
  metadata: Record<string, unknown>;
};

export type TrackEventInput = {
  eventName: AnalyticsEventName;
  page: string;
  feature: string;
  metadata?: Record<string, unknown>;
  onceKey?: string;
};
