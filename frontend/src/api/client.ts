/**
 * Axios API 客户端配置
 */
import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { message } from 'antd';

// 错误响应类型定义
interface ErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: '/api',  // 使用 Vite 代理
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
client.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error: AxiosError<ErrorResponse>) => {
    // 统一错误处理
    const status = error.response?.status;
    const errorData = error.response?.data;

    // 安全地提取错误消息
    let errMsg = '请求失败';
    if (typeof errorData === 'string') {
      errMsg = errorData;
    } else if (errorData) {
      errMsg = errorData.detail || errorData.message || errorData.error || errMsg;
    } else if (error.message) {
      errMsg = error.message;
    }

    switch (status) {
      case 400:
        message.error(`请求参数错误: ${errMsg}`);
        break;
      case 401:
        message.error('未授权，请重新登录');
        break;
      case 403:
        message.error('拒绝访问');
        break;
      case 404:
        message.error('请求的资源不存在');
        break;
      case 409:
        message.error(errMsg);
        break;
      case 500:
        message.error(`服务器错误: ${errMsg}`);
        break;
      default:
        if (errMsg !== '请求取消') {
          message.error(errMsg);
        }
    }

    return Promise.reject(error);
  }
);

export default client;

// =============================================================================
// API 接口定义
// =============================================================================

import type {
  Keyword,
  KeywordWithItems,
  KeywordStats,
  ItemListResponse,
  Item,
  TrendWithKeyword,
  RisingKeyword,
  KeywordTrend,
  CrawlerStatus,
  CrawlerRunResponse,
  CrawlerPlatform,
} from '@/types';

// 关键词 API
export const keywordApi = {
  // 获取关键词榜单
  list: (params?: { limit?: number; category?: string; min_count?: number }) =>
    client.get<Keyword[]>('/keywords', { params }),

  // 获取关键词统计
  getStats: () => client.get<KeywordStats>('/keywords/stats'),

  // 获取关键词详情
  getDetail: (id: number, limit?: number) =>
    client.get<KeywordWithItems>(`/keywords/${id}`, { params: { limit } }),

  // 更新关键词分类
  update: (id: number, data: { category: string }) =>
    client.patch<Keyword>(`/keywords/${id}`, data),

  // 删除关键词
  delete: (id: number) => client.delete(`/keywords/${id}`),
};

// 内容 API
export const itemApi = {
  // 获取内容列表
  list: (params?: {
    page?: number;
    page_size?: number;
    platform?: string;
    min_score?: number;
    keyword_id?: number;
  }) => client.get<ItemListResponse>('/items', { params }),

  // 获取最近内容
  getRecent: (params?: { limit?: number; platform?: string; hours?: number }) =>
    client.get<Item[]>('/items/recent', { params }),

  // 获取内容详情
  getDetail: (id: number) => client.get<Item>(`/items/${id}`),

  // 获取内容关联的关键词
  getKeywords: (id: number) => client.get<Array<{ id: number; word: string; count: number; category: string | null; score: number | null }>>(`/items/${id}/keywords`),
};

// 趋势 API
export const trendApi = {
  // 获取指定日期的趋势
  getDaily: (date: string, limit?: number) =>
    client.get<TrendWithKeyword[]>(`/trends/daily/${date}`, { params: { limit } }),

  // 获取最近趋势
  getRecent: (days?: number) =>
    client.get<Record<string, TrendWithKeyword[]>>('/trends/recent', { params: { days } }),

  // 获取上升趋势关键词
  getRising: (days?: number, limit?: number) =>
    client.get<RisingKeyword[]>('/trends/rising', { params: { days, limit } }),

  // 获取热门关键词
  getHot: (days?: number, limit?: number) =>
    client.get<Array<{ id: number; word: string; count: number; category: string | null }>>('/trends/hot', { params: { days, limit } }),

  // 触发趋势分析
  analyze: (date?: string) =>
    client.post<{ success: boolean; message: string; date: string; count: number }>('/trends/analyze', null, { params: { date } }),

  // 获取关键词趋势历史
  getKeywordTrend: (id: number, days?: number) =>
    client.get<KeywordTrend>(`/trends/keyword/${id}`, { params: { days } }),
};

// 爬虫 API
export const crawlerApi = {
  // 获取爬虫状态
  getStatus: () => client.get<CrawlerStatus>('/crawler/status'),

  // 运行爬虫
  run: (data: { platform: string; limit?: number; save?: boolean; analyze?: boolean }) =>
    client.post<CrawlerRunResponse>('/crawler/run', null, { params: data }),

  // 分析现有数据
  analyze: (limit?: number) =>
    client.post<{ success: boolean; items_analyzed: number; total_keywords: number; message: string }>('/crawler/analyze', null, { params: { limit } }),

  // 获取支持的平台
  getPlatforms: () =>
    client.get<{ platforms: CrawlerPlatform[] }>('/crawler/platforms'),
};
