export type GtmHeadline = {
  window_days: number;
  computed_at: string;
  traffic_sessions: number;
  signups: number;
  activated_users: number;
  paid_users: number;
  revenue_usd: number;
  spend_usd: number;
  blended_cac_usd: number | null;
  blended_roi_percent: number | null;
};

export type GtmChannelPerformance = {
  source: string;
  campaign: string | null;
  traffic_sessions: number;
  ad_clicks: number;
  landing_views: number;
  signups: number;
  activated_users: number;
  paid_users: number;
  revenue_usd: number;
  spend_usd: number;
  signup_rate: number;
  activation_rate: number;
  conversion_rate: number;
  cac_usd: number | null;
  roi_percent: number | null;
  ltv_cac_proxy: number | null;
};

export type GtmSourceFunnel = {
  source: string;
  acquired: number;
  signed_up: number;
  activated: number;
  paid: number;
  acquired_to_signup: number;
  signup_to_activated: number;
  activated_to_paid: number;
};

export type GtmCreativePerformance = {
  source: string;
  campaign: string | null;
  ad_id: string | null;
  creative_id: string | null;
  clicks: number;
  signups: number;
  activated_users: number;
  paid_users: number;
  revenue_usd: number;
  conversion_rate: number;
};

export type GtmScaleSignal = {
  signal: "scale_channel" | "kill_channel";
  source: string;
  campaign: string | null;
  reason: string;
  roi_percent: number | null;
  cac_usd: number | null;
  conversion_rate: number;
};

export type ChannelSpendUpsertWrite = {
  spend_day: string;
  source: string;
  medium?: string | null;
  campaign?: string | null;
  ad_id?: string | null;
  creative_id?: string | null;
  cost_usd: number;
  clicks?: number;
  impressions?: number;
  dedupe_key?: string | null;
};

export type ChannelSpendUpsertRead = {
  id: string;
  spend_day: string;
  source: string;
  medium: string | null;
  campaign: string | null;
  ad_id: string | null;
  creative_id: string | null;
  cost_usd: number;
  clicks: number;
  impressions: number;
  dedupe_key: string;
  updated_at: string;
};

export type GtmDashboard = {
  headline: GtmHeadline;
  channels: GtmChannelPerformance[];
  funnel_by_source: GtmSourceFunnel[];
  top_campaigns: GtmChannelPerformance[];
  top_creatives: GtmCreativePerformance[];
  signals: GtmScaleSignal[];
};
