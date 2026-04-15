/**
 * API 数据类型定义
 */

// =============================================================================
// 关键词相关
// =============================================================================

export interface Keyword {
  id: number;
  word: string;
  count: number;
  category: string | null;
  first_seen: string;
  last_seen: string;
}

export interface KeywordWithItems extends Keyword {
  items: ItemLite[];
}

export interface KeywordStats {
  total: number;
  by_category: Record<string, number>;
}

// =============================================================================
// 内容相关
// =============================================================================

export interface Item {
  id: number;
  platform: string;
  title: string;
  content: string | null;
  url: string;
  score: number;
  comment_count: number;
  author: string | null;
  created_at: string;
  crawled_at: string;
}

export interface ItemLite {
  id: number;
  title: string;
  platform: string;
  score: number;
  url: string;
}

export interface ItemListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Item[];
}

// =============================================================================
// 趋势相关
// =============================================================================

export interface Trend {
  id: number;
  keyword_id: number;
  date: string;
  count: number;
  avg_score: number | null;
  keyword?: KeywordBase;
}

export interface KeywordBase {
  word: string;
  category?: string | null;
}

export interface TrendWithKeyword {
  date: string;
  keyword: string;
  count: number;
  avg_score: number | null;
}

export interface RisingKeyword {
  keyword: string;
  current_count: number;
  previous_count: number;
  growth_rate: number;
  avg_score: number;
}

export interface KeywordTrend {
  keyword: string;
  keyword_id: number;
  category: string | null;
  trends: Array<{
    date: string;
    count: number;
    avg_score: number | null;
  }>;
}

// =============================================================================
// 爬虫相关
// =============================================================================

export interface CrawlerStatus {
  is_running: boolean;
  platform: string | null;
  last_run: string | null;
  last_count: number | null;
}

export interface CrawlerRunRequest {
  platform: string;
  limit: number;
}

export interface CrawlerRunResponse {
  success: boolean;
  platform: string;
  count: number;
  message: string;
}

export interface CrawlerPlatform {
  name: string;
  display_name: string;
  description: string;
  enabled: boolean;
}

// =============================================================================
// 通用
// =============================================================================

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T | null;
}

export type CategoryType =
  | "TOOL"
  | "CONTENT"
  | "SERVICE"
  | "PRODUCT"
  | "LIFESTYLE"
  | "CAREER"
  | "OTHER";

export const CATEGORY_LABELS: Record<CategoryType, string> = {
  TOOL: "工具类",
  CONTENT: "内容类",
  SERVICE: "服务类",
  PRODUCT: "实物类",
  LIFESTYLE: "生活类",
  CAREER: "职业类",
  OTHER: "其他",
};

export const CATEGORY_COLORS: Record<string, string> = {
  TOOL: "#1890ff",
  CONTENT: "#52c41a",
  SERVICE: "#fa8c16",
  PRODUCT: "#eb2f96",
  LIFESTYLE: "#722ed1",
  CAREER: "#13c2c2",
  OTHER: "#d9d9d9",
};
