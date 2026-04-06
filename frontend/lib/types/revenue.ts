export type RevenueHeadline = {
  window_days: number;
  computed_at: string;
  mrr_usd: number;
  arr_usd: number;
  arpu_usd: number;
  free_to_paid_conversion: number;
  revenue_per_user_usd: number;
  ltv_proxy_usd: number;
  churn_rate: number;
  paying_user_retention_d30: number;
};

export type RevenueFunnelStep = {
  key: string;
  label: string;
  users: number;
  conversion_from_prev: number;
  dropoff_from_prev: number;
};

export type RevenueFunnel = {
  steps: RevenueFunnelStep[];
};

export type RevenueSource = {
  source: string;
  acquired_users: number;
  paid_users: number;
  conversion_rate: number;
  mrr_usd: number;
  arr_usd: number;
};

export type RevenueCohort = {
  cohort_week_start: string;
  source: string;
  plan_tier: string;
  users: number;
  paid_users: number;
  revenue_usd: number;
  retention_d30: number | null;
  conversion_lag_days: number | null;
};

export type RevenueExperimentVariant = {
  experiment_key: string;
  variant: string;
  views: number;
  interactions: number;
  upgrades: number;
  paid_users: number;
  conversion_rate: number;
  revenue_per_user_usd: number;
  retention_d30: number;
};

export type RevenueChurnSignal = {
  churn_risk_users: number;
  canceled_users: number;
  inactive_paying_users: number;
  generated_at: string;
};

export type RevenueDashboard = {
  headline: RevenueHeadline;
  funnel: RevenueFunnel;
  funnel_by_source: RevenueSource[];
  revenue_by_source: RevenueSource[];
  paywall_performance: RevenueExperimentVariant[];
  cohorts: RevenueCohort[];
  churn_signals: RevenueChurnSignal;
};

