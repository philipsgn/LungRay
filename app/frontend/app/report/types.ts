// ============================================================================
// LUNGRAY INTERACTIVE REPORT TYPE DEFINITIONS
// ============================================================================

export type Language = "en" | "vi";

export interface BilingualText {
  en: string;
  vi: string;
}

export interface MetricCounterItem {
  id: string;
  label: BilingualText;
  value: number;
  decimals: number;
  prefix?: string;
  suffix?: string;
  subtext: BilingualText;
  badge?: BilingualText;
}

export interface DatasetItem {
  id: string;
  name: string;
  images: number;
  patients: number | string;
  classes: number;
  role: BilingualText;
  splitProtocol: BilingualText;
  leakageRate: string;
  badge: string;
  category: "all" | "primary" | "groundtruth" | "ood";
}

export interface ImbalanceDataPoint {
  task: string;
  taskLabel: BilingualText;
  rawCount: number;
  rawPct: number;
  balancedPct: number;
  fillRaw: string;
  fillBalanced: string;
}

export interface PipelineStepItem {
  step: string;
  title: BilingualText;
  subtitle: BilingualText;
  description: BilingualText;
  details: BilingualText[];
  codeSnippet: string;
}

export interface ArchitectureNode {
  id: string;
  label: BilingualText;
  tensorDim: string;
  params: string;
  activation: string;
  color: "sky" | "emerald" | "amber" | "slate" | "indigo";
  modulePath: string;
  lossFn?: string;
  description: BilingualText;
  rationale: BilingualText;
}

export interface TrainingEpochRecord {
  epoch: number;
  trainLoss: number;
  lossA: number;
  lossB: number;
  lossC: number;
  valAucA: number;
  valAucB: number;
  valAucC: number;
  valScore: number;
  lr: number;
  stageName: BilingualText;
  isBestCheckpoint?: boolean;
}

export interface ConfusionMatrixData {
  labels: string[];
  matrix: number[][]; // [row][col] normalized
  sampleCounts: number[][]; // [row][col] raw counts
  clinicalConsequences: {
    cell: [number, number];
    explanation: BilingualText;
  }[];
}

export interface RocCurvePoint {
  fpr: number;
  headA: number;
  headB: number;
  headC: number;
}

export interface DiseaseLeaderboardItem {
  disease: string;
  diseaseVi: string;
  auroc: number;
  ci95: [number, number];
  threshold: number;
  chexnet: number;
  prevalence: string;
}

export interface ModelComparisonSpec {
  architecture: string;
  paramsM: number;
  sizeMB: number;
  latencyCpuMs: number;
  latencyGpuMs: number;
  macroAuroc: number;
  headA: number;
  headB: number;
  headC: number;
  clinicalFeasibility: BilingualText;
}

export interface ShortcutAuditData {
  sampleSize: number;
  unmasked: {
    meanRatio: number;
    stdRatio: number;
    minRatio: number;
    maxRatio: number;
    passRate: number;
  };
  clinicalGrounding: {
    meanRatio: number;
    stdRatio: number;
    minRatio: number;
    maxRatio: number;
    passRate: number;
  };
  deltaGain: number;
  wilcoxonStat: number;
  wilcoxonPValue: number;
}

export interface CheXpertOodItem {
  pathology: string;
  nihAuc: number;
  chexpertAuc: number;
  delta: number;
  retention: number;
  pass: boolean;
}

export interface ErrorCaseItem {
  id: string;
  patientId: string;
  targetDisease: BilingualText;
  groundTruth: BilingualText;
  predictedProb: number;
  predictionLabel: BilingualText;
  boxIou?: number;
  inLungEnergyPct: number;
  radiologistNotes: BilingualText;
  caseType: "fp" | "fn" | "tp";
}
