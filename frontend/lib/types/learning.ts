import type { EconomyAction } from "./economy";

export type LessonListItem = {
  id: string;
  slug: string;
  title: string;
  min_tier: string;
  sort_order: number;
  created_at: string;
  locked: boolean;
};

export type PopularLessonItem = LessonListItem & {
  completion_count: number;
};

export type LessonDetail = LessonListItem & {
  body: string;
  body_locked?: boolean;
};

export type LearningProgressStatus = "not_started" | "active" | "completed";
export type LearningLessonStatus = "not_started" | "in_progress" | "completed";
export type LearningStepKind =
  | "theory"
  | "guided_practice"
  | "quiz"
  | "applied_exercise"
  | "reflection"
  | "final_checkpoint";

export type LearningStartTarget = {
  target: string;
  has_active_course: boolean;
  active_course_slug?: string | null;
  resume_href?: string | null;
};

export type LearningActionLink = {
  label: string;
  href: string;
  body?: string | null;
};

export type LearningCourseCard = {
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  difficulty: string;
  result_headline?: string | null;
  deliverable_preview?: string | null;
  estimated_minutes: number;
  module_count: number;
  lesson_count: number;
  progress_percent: number;
  status: LearningProgressStatus;
  last_activity_at?: string | null;
  next_lesson_slug?: string | null;
  resume_href?: string | null;
  badge_earned: boolean;
  course_reward_lmn: number;
};

export type LearningCatalog = {
  courses: LearningCourseCard[];
  recommended_course_slug?: string | null;
};

export type LearningWeakArea = {
  tag: string;
  count: number;
  recommendation: string;
  lesson_slug?: string | null;
};

export type LearningMyCourseItem = {
  slug: string;
  title: string;
  subtitle: string;
  progress_percent: number;
  status: LearningProgressStatus;
  last_activity_at?: string | null;
  next_lesson_title?: string | null;
  next_lesson_slug?: string | null;
  continue_href?: string | null;
  completed_at?: string | null;
  badge_code?: string | null;
  certificate_ready: boolean;
};

export type LearningMyModules = {
  active_courses: LearningMyCourseItem[];
  completed_courses: LearningMyCourseItem[];
  weak_areas: LearningWeakArea[];
};

export type LearningLessonOutline = {
  slug: string;
  title: string;
  summary: string;
  estimated_minutes: number;
  position: number;
  status: LearningLessonStatus;
  unlocked: boolean;
  is_final_assessment: boolean;
  progress_percent: number;
  continue_href: string;
};

export type LearningModule = {
  slug: string;
  title: string;
  summary: string;
  position: number;
  lesson_count: number;
  progress_percent: number;
  lessons: LearningLessonOutline[];
};

export type LearningCourseRewards = {
  lesson_reward_lmn: number;
  course_reward_lmn: number;
  badge_code: string;
  certificate_template: string;
  badge_earned: boolean;
  course_completed: boolean;
};

export type LearningCourseDetail = {
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  difficulty: string;
  result_headline?: string | null;
  estimated_minutes: number;
  module_count: number;
  lesson_count: number;
  progress_percent: number;
  status: LearningProgressStatus;
  last_activity_at?: string | null;
  resume_href?: string | null;
  start_or_continue_label: string;
  what_you_will_learn: string[];
  prerequisites: string[];
  deliverables: string[];
  career_outcomes: string[];
  product_action?: LearningActionLink | null;
  modules: LearningModule[];
  rewards: LearningCourseRewards;
  weak_areas: LearningWeakArea[];
};

export type LearningStepChoice = {
  id: string;
  text: string;
  explanation?: string | null;
};

export type LearningQuizQuestion = {
  id: string;
  question: string;
  choices: LearningStepChoice[];
};

export type LearningStepFeedback = {
  verdict: string;
  score: number;
  pass_score: number;
  strengths: string[];
  improvements: string[];
  revisit: string[];
  hint?: string | null;
};

export type LearningLessonStep = {
  slug: string;
  kind: LearningStepKind;
  title: string;
  estimated_minutes: number;
  content: string[];
  task?: string | null;
  placeholder?: string | null;
  question?: string | null;
  choices: LearningStepChoice[];
  quiz_questions: LearningQuizQuestion[];
  pass_score: number;
  min_words?: number | null;
  required_markers: string[];
  bonus_markers: string[];
  forbidden_phrases: string[];
  submission_type: "none" | "text" | "choice";
  unlocked: boolean;
  completed: boolean;
  attempts: number;
  last_score?: number | null;
  last_answer_text?: string | null;
  last_choice_id?: string | null;
  last_choice_map: Record<string, string>;
  feedback?: LearningStepFeedback | null;
};

export type LearningLessonDetail = {
  course_slug: string;
  module_slug: string;
  lesson_slug: string;
  title: string;
  summary: string;
  objective?: string | null;
  deliverable?: string | null;
  scenario_title?: string | null;
  scenario_body?: string | null;
  debrief: string[];
  review_rubric: string[];
  common_mistakes: string[];
  estimated_minutes: number;
  position_in_course: number;
  total_lessons: number;
  progress_percent: number;
  course_progress_percent: number;
  status: LearningLessonStatus;
  unlocked: boolean;
  is_final_assessment: boolean;
  return_to_course_href: string;
  previous_lesson_href?: string | null;
  next_lesson_href?: string | null;
  steps: LearningLessonStep[];
  current_step_slug?: string | null;
  lesson_list: LearningLessonOutline[];
};

export type LearningStepSubmitResponse = {
  course_slug: string;
  module_slug: string;
  lesson_slug: string;
  step_slug: string;
  passed: boolean;
  completed: boolean;
  score: number;
  attempts: number;
  feedback: LearningStepFeedback;
  lesson_progress_percent: number;
  course_progress_percent: number;
  lesson_completed: boolean;
  course_completed: boolean;
  next_step_slug?: string | null;
  next_lesson_slug?: string | null;
  resume_href: string;
  weak_areas: LearningWeakArea[];
  awarded_lmn: number;
  awarded_badge?: string | null;
  certificate_ready: boolean;
  economy?: EconomyAction | null;
};
