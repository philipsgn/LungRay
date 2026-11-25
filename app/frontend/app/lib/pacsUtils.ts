import type { StudyRecord } from "../components/StudyWorklistDrawer";

export function cardiothoracicRatio(cardiacWidth: number, thoracicWidth: number): number {
  return Math.abs(cardiacWidth) / Math.max(0.1, Math.abs(thoracicWidth));
}
export function csvRow(values: (string | number)[]): string {
  return values.map(value => `"${String(value).replace(/"/g, '""')}"`).join(",");
}
export function filterStudies(studies: StudyRecord[], query: string, priority: string): StudyRecord[] {
  const text = query.trim().toLowerCase();
  return studies.filter(study => (priority === "ALL" || study.priority === priority) &&
    (!text || [study.studyId, study.patientId, study.indication].some(value => value.toLowerCase().includes(text))));
}
