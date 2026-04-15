/**
 * Zustand 全局状态管理
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Keyword, Item, CrawlerStatus, CategoryType } from '@/types';
import { keywordApi, crawlerApi } from '@/api/client';

// =============================================================================
// App Store - 应用全局状态
// =============================================================================

interface AppState {
  // 侧边栏状态
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // 加载状态
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;

  // 当前选中的分类
  selectedCategory: CategoryType | 'all';
  setSelectedCategory: (category: CategoryType | 'all') => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // 侧边栏
      sidebarCollapsed: false,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // 加载状态
      globalLoading: false,
      setGlobalLoading: (loading) => set({ globalLoading: loading }),

      // 分类筛选
      selectedCategory: 'all',
      setSelectedCategory: (category) => set({ selectedCategory: category }),
    }),
    { name: 'AppStore' }
  )
);

// =============================================================================
// Keyword Store - 关键词状态
// =============================================================================

interface KeywordState {
  keywords: Keyword[];
  loading: boolean;
  error: string | null;
  total: number;
  categoryStats: Record<string, number>;

  // Actions
  setKeywords: (keywords: Keyword[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setTotal: (total: number) => void;
  setCategoryStats: (stats: Record<string, number>) => void;

  // 刷新关键词列表
  refreshKeywords: (params?: { limit?: number; category?: string }) => Promise<void>;
}

export const useKeywordStore = create<KeywordState>()(
  devtools(
    (set) => ({
      // State
      keywords: [],
      loading: false,
      error: null,
      total: 0,
      categoryStats: {},

      // Setters
      setKeywords: (keywords) => set({ keywords }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setTotal: (total) => set({ total }),
      setCategoryStats: (stats) => set({ categoryStats: stats }),

      // Actions
      refreshKeywords: async (params) => {
        set({ loading: true, error: null });
        try {
          const [keywords, stats] = await Promise.all([
            keywordApi.list(params),
            keywordApi.getStats(),
          ]);
          set({
            keywords,
            total: stats.total,
            categoryStats: stats.by_category,
            loading: false,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : '加载失败';
          set({
            error: errorMessage,
            loading: false,
          });
          // 重新抛出错误以便调用方处理
          throw error;
        }
      },
    }),
    { name: 'KeywordStore' }
  )
);

// =============================================================================
// Crawler Store - 爬虫状态
// =============================================================================

interface CrawlerState {
  status: CrawlerStatus;
  loading: boolean;

  // Actions
  setStatus: (status: CrawlerStatus) => void;
  setLoading: (loading: boolean) => void;

  // 刷新状态
  refreshStatus: () => Promise<void>;

  // 运行爬虫
  runCrawler: (platform: string, limit?: number) => Promise<void>;
}

export const useCrawlerStore = create<CrawlerState>()(
  devtools(
    (set, get) => ({
      // State
      status: {
        is_running: false,
        platform: null,
        last_run: null,
        last_count: 0,
      },
      loading: false,

      // Setters
      setStatus: (status) => set({ status }),
      setLoading: (loading) => set({ loading }),

      // Actions
      refreshStatus: async () => {
        try {
          const status = await crawlerApi.getStatus();
          set({ status });
        } catch (error) {
          console.error('获取爬虫状态失败:', error);
          throw error;
        }
      },

      runCrawler: async (platform, limit = 10) => {
        set({ loading: true });
        try {
          await crawlerApi.run({ platform, limit });
          // 运行后刷新状态
          await get().refreshStatus();
        } finally {
          set({ loading: false });
        }
      },
    }),
    { name: 'CrawlerStore' }
  )
);

// =============================================================================
// UI Store - UI 状态
// =============================================================================

interface UIState {
  // 关键词详情弹窗
  keywordDetailVisible: boolean;
  selectedKeywordId: number | null;
  showKeywordDetail: (id: number) => void;
  hideKeywordDetail: () => void;

  // 搜索关键词
  searchKeyword: string;
  setSearchKeyword: (keyword: string) => void;

  // 日期范围
  dateRange: [string, string] | null;
  setDateRange: (range: [string, string] | null) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      // 关键词详情弹窗
      keywordDetailVisible: false,
      selectedKeywordId: null,
      showKeywordDetail: (id) => set({
        keywordDetailVisible: true,
        selectedKeywordId: id,
      }),
      hideKeywordDetail: () => set({
        keywordDetailVisible: false,
        selectedKeywordId: null,
      }),

      // 搜索
      searchKeyword: '',
      setSearchKeyword: (keyword) => set({ searchKeyword: keyword }),

      // 日期范围
      dateRange: null,
      setDateRange: (range) => set({ dateRange: range }),
    }),
    { name: 'UIStore' }
  )
);
