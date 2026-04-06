export type GrowthMetricSnapshot = {
  window_days: number;
  computed_at: string;
  activation_rate: number;
  d1_retention: number;
  d7_retention: number;
  free_to_paid_conversion: number;
  upgrade_intent_rate: number;
  ltv_proxy_usd: number;
};

export type GrowthFunnelStep = {
  key: string;
  label: string;
  users: number;
  conversion_from_prev: number;
};

export type GrowthFunnel = {
  window_days: number;
  steps: GrowthFunnelStep[];
};

export type GrowthCohort = {
  cohort_week_start: string;
  users: number;
  d1_retention: number;
  d7_retention: number | null;
  paid_30d_conversion: number | null;
};

export type GrowthExperimentVariant = {
  variant: string;
  users: number;
  conversion: number;
  retention_d7: number;
};

export type GrowthExperiment = {
  key: string;
  rollout_percent: number;
  variants: GrowthExperimentVariant[];
};

export type GrowthFlag = {
  key: string;
  enabled: boolean;
  rollout_percent: number;
  target: string;
  reason: string;
};

export type GrowthExperimentAssignment = {
  key: string;
  variant: string;
  rollout_percent: number;
  eligible: boolean;
  reason: string;
};

export type GrowthRuntime = {
  computed_at: string;
  session_id: string;
  flags: GrowthFlag[];
  experiments: GrowthExperimentAssignment[];
};

export type GrowthDashboard = {
  metrics: GrowthMetricSnapshot;
  funnel: GrowthFunnel;
  cohorts: GrowthCohort[];
  experiments: GrowthExperiment[];
  rollout_flags: GrowthFlag[];
};

