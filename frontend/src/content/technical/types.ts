import type { ComponentType } from "react";

export interface TechSectionMeta {
  id: string;
  title: string;
  group: "Nền tảng" | "Phân tích" | "Vận hành" | "Tham chiếu";
  order: number;
  keywords: string;
}

export interface TechSection extends TechSectionMeta {
  Component: ComponentType;
}

export interface TocEntry {
  id: string;
  title: string;
  level: 2 | 3;
  sectionId: string;
}
