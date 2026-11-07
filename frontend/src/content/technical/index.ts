import type { TechSection } from "./types";
import { TECH_MANIFEST } from "./manifest";
import TongQuan from "./sections/01-tong-quan";
import CopyTrading from "./sections/02-copy-trading";
import KienTruc from "./sections/03-kien-truc";
import DuLieu from "./sections/04-du-lieu";
import Tier from "./sections/05-tier";
import ChiSo from "./sections/06-chi-so";
import Scoring from "./sections/07-scoring";
import Risk from "./sections/08-risk";
import Ranking from "./sections/09-ranking";
import Compare from "./sections/10-compare";
import DataHealth from "./sections/11-data-health";
import Ai from "./sections/12-ai";
import Settings from "./sections/13-settings";
import ApiBaoMat from "./sections/14-api-bao-mat";
import VanHanh from "./sections/15-van-hanh";
import Testing from "./sections/16-testing";
import Glossary from "./sections/17-glossary";
import Faq from "./sections/18-faq";
import GioiHan from "./sections/19-gioi-han";
import Changelog from "./sections/20-changelog";

const COMPONENTS = {
  "tong-quan": TongQuan,
  "copy-trading": CopyTrading,
  "kien-truc": KienTruc,
  "du-lieu": DuLieu,
  tier: Tier,
  "chi-so": ChiSo,
  scoring: Scoring,
  risk: Risk,
  ranking: Ranking,
  compare: Compare,
  "data-health": DataHealth,
  ai: Ai,
  settings: Settings,
  "api-bao-mat": ApiBaoMat,
  "van-hanh": VanHanh,
  testing: Testing,
  glossary: Glossary,
  faq: Faq,
  "gioi-han": GioiHan,
  changelog: Changelog,
} as const;

export const TECH_SECTIONS: TechSection[] = TECH_MANIFEST.map((meta) => ({
  ...meta,
  Component: COMPONENTS[meta.id as keyof typeof COMPONENTS],
}));

export const TECH_GROUPS = ["Nền tảng", "Phân tích", "Vận hành", "Tham chiếu"] as const;
