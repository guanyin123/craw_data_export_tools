/**
 * 趋势分析页面
 * 展示关键词的时间维度趋势、上升/下降趋势
 */
import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  Table,
  Tag,
  Space,
  Statistic,
  Spin,
  Tabs,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  FireOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import TrendChart, { SimpleTrendChart, type TrendChartData } from '@/components/TrendChart';
import { trendApi } from '@/api/client';
import type { RisingKeyword, KeywordTrend } from '@/types';
import { CATEGORY_LABELS, CATEGORY_COLORS } from '@/types';

// 复用 @/types 中的 KeywordTrend 类型
type AggregatedTrend = KeywordTrend;

const DAYS_OPTIONS = [
  { label: '最近 3 天', value: 3 },
  { label: '最近 7 天', value: 7 },
  { label: '最近 14 天', value: 14 },
  { label: '最近 30 天', value: 30 },
];

export default function Trends() {
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState<number>(7);
  const [risingKeywords, setRisingKeywords] = useState<RisingKeyword[]>([]);
  const [hotKeywords, setHotKeywords] = useState<
    Array<{ id: number; word: string; count: number; category: string | null }>
  >([]);
  const [recentTrends, setRecentTrends] = useState<Record<string, Array<{
    date: string;
    keyword: string;
    count: number;
    avg_score: number | null;
  }>>>({});
  const [activeTab, setActiveTab] = useState<'rising' | 'hot' | 'chart'>('chart');

  // 使用 ref 跟踪组件挂载状态和初始加载
  const mountedRef = useRef(false);
  const initialLoadRef = useRef(true);

  // 加载上升趋势关键词
  const loadRisingKeywords = useCallback(async (daysParam: number) => {
    try {
      const data = await trendApi.getRising(daysParam, 20);
      setRisingKeywords(data);
    } catch {
      // Error handled by API client
    }
  }, []);

  // 加载热门关键词
  const loadHotKeywords = useCallback(async (daysParam: number) => {
    try {
      const data = await trendApi.getHot(daysParam, 20);
      setHotKeywords(data);
    } catch {
      // Error handled by API client
    }
  }, []);

  // 加载最近趋势数据
  const loadRecentTrends = useCallback(async (daysParam: number) => {
    try {
      const data = await trendApi.getRecent(daysParam);
      setRecentTrends(data);
    } catch {
      // Error handled by API client
    }
  }, []);

  // 加载所有数据
  const loadAllData = useCallback(
    async (daysParam: number) => {
      setLoading(true);
      try {
        await Promise.all([
          loadRisingKeywords(daysParam),
          loadHotKeywords(daysParam),
          loadRecentTrends(daysParam),
        ]);
      } finally {
        if (mountedRef.current) {
          setLoading(false);
        }
      }
    },
    [loadRisingKeywords, loadHotKeywords, loadRecentTrends]
  );

  // 初始化加载
  useEffect(() => {
    mountedRef.current = true;
    loadAllData(days);

    return () => {
      mountedRef.current = false;
    };
    // 仅在初始化时执行
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 聚合趋势数据 - 优化版本，避免多次 reduce
  const aggregateTrendData = useMemo<AggregatedTrend[]>(() => {
    const keywordMap = new Map<
      string,
      {
        keyword_id: number;
        category: string | null;
        trends: Map<string, { count: number; avg_score: number | null }>;
      }
    >();

    // 构建关键词映射
    Object.entries(recentTrends).forEach(([date, trends]) => {
      trends.forEach((trend) => {
        if (!keywordMap.has(trend.keyword)) {
          keywordMap.set(trend.keyword, {
            keyword_id: 0,
            category: null,
            trends: new Map(),
          });
        }
        const entry = keywordMap.get(trend.keyword)!;
        entry.trends.set(date, {
          count: trend.count,
          avg_score: trend.avg_score,
        });
      });
    });

    // 转换为数组，一次性计算 total
    const result: Array<AggregatedTrend & { total: number }> = Array.from(
      keywordMap.entries()
    ).map(([keyword, data]) => {
      const trends = Array.from(data.trends.entries())
        .map(([date, values]) => ({
          date,
          count: values.count,
          avg_score: values.avg_score,
        }))
        .sort((a, b) => a.date.localeCompare(b.date));

      // 只计算一次 total
      const total = trends.reduce((sum, t) => sum + t.count, 0);

      return {
        keyword,
        keyword_id: data.keyword_id,
        category: data.category,
        trends,
        total,
      };
    });

    // 使用预计算的 total 进行排序
    result.sort((a, b) => b.total - a.total);

    // 移除 total 字段，返回标准 AggregatedTrend 类型
    return result.slice(0, 20).map(({ total, ...rest }) => rest);
  }, [recentTrends]);

  const handleDaysChange = useCallback(
    (value: number) => {
      setDays(value);
      loadAllData(value);
    },
    [loadAllData]
  );

  // 上升趋势表格列
  const risingColumns: ColumnsType<RisingKeyword> = useMemo(
    () => [
      {
        title: '排名',
        key: 'rank',
        width: 70,
        render: (_: unknown, __: unknown, index: number) => (
          <span style={{ fontWeight: 600, color: index < 3 ? '#1890ff' : undefined }}>
            #{index + 1}
          </span>
        ),
      },
      {
        title: '关键词',
        dataIndex: 'keyword',
        key: 'keyword',
        width: 150,
        render: (text: string) => <strong>{text}</strong>,
      },
      {
        title: '当前次数',
        dataIndex: 'current_count',
        key: 'current_count',
        width: 100,
        sorter: (a, b) => a.current_count - b.current_count,
        render: (value: number) => value.toLocaleString(),
      },
      {
        title: '之前次数',
        dataIndex: 'previous_count',
        key: 'previous_count',
        width: 100,
        render: (value: number) => value.toLocaleString(),
      },
      {
        title: '增长率',
        dataIndex: 'growth_rate',
        key: 'growth_rate',
        width: 120,
        sorter: (a, b) => a.growth_rate - b.growth_rate,
        render: (value: number) => (
          <Space>
            <ArrowUpOutlined style={{ color: '#52c41a' }} />
            <span style={{ color: '#52c41a', fontWeight: 600 }}>
              {value > 0 ? '+' : ''}
              {value.toFixed(1)}%
            </span>
          </Space>
        ),
      },
      {
        title: '平均热度',
        dataIndex: 'avg_score',
        key: 'avg_score',
        width: 100,
        sorter: (a, b) => a.avg_score - b.avg_score,
        render: (value: number) => Math.round(value).toLocaleString(),
      },
    ],
    []
  );

  // 热门关键词表格列
  const hotColumns: ColumnsType<{
    id: number;
    word: string;
    count: number;
    category: string | null;
  }> = useMemo(
    () => [
      {
        title: '排名',
        key: 'rank',
        width: 70,
        render: (_: unknown, __: unknown, index: number) => (
          <span style={{ fontWeight: 600 }}>
            {index < 3 ? (
              <FireOutlined
                style={{
                  color: index === 0 ? '#ff4d4f' : index === 1 ? '#faad14' : '#52c41a',
                }}
              />
            ) : (
              `#${index + 1}`
            )}
          </span>
        ),
      },
      {
        title: '关键词',
        dataIndex: 'word',
        key: 'word',
        width: 150,
        render: (text: string) => <strong>{text}</strong>,
      },
      {
        title: '分类',
        dataIndex: 'category',
        key: 'category',
        width: 100,
        render: (category: string | null) =>
          category ? (
            <Tag color={CATEGORY_COLORS[category] || 'default'}>
              {CATEGORY_LABELS[category] || category}
            </Tag>
          ) : (
            <Tag>未分类</Tag>
          ),
      },
      {
        title: '总出现次数',
        dataIndex: 'count',
        key: 'count',
        width: 120,
        sorter: (a, b) => a.count - b.count,
        render: (value: number) => <Statistic value={value} valueStyle={{ fontSize: 16 }} />,
      },
      {
        title: '热度趋势',
        key: 'trend',
        width: 150,
        render: (_: unknown, record: { word: string }) => {
          const keywordTrend = aggregateTrendData.find((t) => t.keyword === record.word);
          if (!keywordTrend || keywordTrend.trends.length < 2) {
            return <span style={{ color: '#999' }}>-</span>;
          }

          const latest = keywordTrend.trends[keywordTrend.trends.length - 1].count;
          const previous = keywordTrend.trends[keywordTrend.trends.length - 2].count;
          const change = latest - previous;
          const percent = previous > 0 ? (change / previous) * 100 : 0;

          if (change > 0) {
            return (
              <Space>
                <ArrowUpOutlined style={{ color: '#52c41a' }} />
                <span style={{ color: '#52c41a' }}>+{percent.toFixed(1)}%</span>
              </Space>
            );
          } else if (change < 0) {
            return (
              <Space>
                <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
                <span style={{ color: '#ff4d4f' }}>{percent.toFixed(1)}%</span>
              </Space>
            );
          }
          return <MinusOutlined style={{ color: '#999' }} />;
        },
      },
    ],
    [aggregateTrendData]
  );

  // 计算统计数据
  const stats = useMemo(() => {
    const risingCount = risingKeywords.filter((k) => k.growth_rate > 50).length;
    const totalRisingGrowth = risingKeywords.reduce((sum, k) => sum + k.growth_rate, 0);
    const avgRisingGrowth = risingKeywords.length > 0 ? totalRisingGrowth / risingKeywords.length : 0;

    return {
      risingCount,
      avgGrowthRate: avgRisingGrowth,
      hotCount: hotKeywords.length,
    };
  }, [risingKeywords, hotKeywords]);

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>趋势分析</h2>
        <Space>
          <span>时间范围:</span>
          <Select
            value={days}
            onChange={handleDaysChange}
            options={DAYS_OPTIONS}
            style={{ width: 120 }}
          />
        </Space>
      </div>

      <Spin spinning={loading}>
        {/* 统计卡片 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="快速增长关键词"
                value={stats.risingCount}
                suffix="个"
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均增长率"
                value={stats.avgGrowthRate}
                suffix="%"
                prefix={<ArrowUpOutlined />}
                valueStyle={{ color: '#1890ff' }}
                precision={1}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="热门关键词"
                value={stats.hotCount}
                suffix="个"
                prefix={<FireOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="数据天数"
                value={days}
                suffix="天"
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 主内容区域 */}
        <Card>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as typeof activeTab)}
            items={[
              {
                key: 'chart',
                label: '趋势图表',
                children: (
                  <div>
                    <div style={{ marginBottom: 16 }}>
                      <h4>热门关键词趋势 (Top 10)</h4>
                    </div>
                    {aggregateTrendData.length > 0 ? (
                      <TrendChart data={aggregateTrendData.slice(0, 10)} height={450} />
                    ) : (
                      <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                        暂无趋势数据，请先运行爬虫并分析数据
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: 'rising',
                label: (
                  <span>
                    上升趋势
                    <Tag color="green" style={{ marginLeft: 8 }}>
                      {risingKeywords.length}
                    </Tag>
                  </span>
                ),
                children: (
                  <div>
                    <div style={{ marginBottom: 16 }}>
                      <p style={{ color: '#666', margin: 0 }}>
                        以下关键词在最近 {days} 天内呈现快速增长趋势，值得关注潜在的商机。
                      </p>
                    </div>
                    <Table
                      rowKey="keyword"
                      columns={risingColumns}
                      dataSource={risingKeywords}
                      pagination={{ pageSize: 10 }}
                      size="small"
                      expandable={{
                        expandedRowRender: (record) => {
                          const keywordTrend = aggregateTrendData.find((t) => t.keyword === record.keyword);
                          return keywordTrend && keywordTrend.trends.length > 1 ? (
                            <div style={{ padding: '16px 0' }}>
                              <SimpleTrendChart
                                data={keywordTrend.trends}
                                keyword={record.keyword}
                                height={200}
                              />
                            </div>
                          ) : null;
                        },
                      }}
                    />
                  </div>
                ),
              },
              {
                key: 'hot',
                label: (
                  <span>
                    热门关键词
                    <Tag color="orange" style={{ marginLeft: 8 }}>
                      {hotKeywords.length}
                    </Tag>
                  </span>
                ),
                children: (
                  <div>
                    <div style={{ marginBottom: 16 }}>
                      <p style={{ color: '#666', margin: 0 }}>
                        以下是在最近 {days} 天内出现频率最高的关键词。
                      </p>
                    </div>
                    <Table
                      rowKey="id"
                      columns={hotColumns}
                      dataSource={hotKeywords}
                      pagination={{ pageSize: 10 }}
                      size="small"
                      expandable={{
                        expandedRowRender: (record) => {
                          const keywordTrend = aggregateTrendData.find((t) => t.keyword === record.word);
                          return keywordTrend && keywordTrend.trends.length > 1 ? (
                            <div style={{ padding: '16px 0' }}>
                              <SimpleTrendChart data={keywordTrend.trends} keyword={record.word} height={200} />
                            </div>
                          ) : null;
                        },
                      }}
                    />
                  </div>
                ),
              },
            ]}
          />
        </Card>
      </Spin>
    </div>
  );
}
