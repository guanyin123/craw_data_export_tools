/**
 * 关键词详情页面
 */
import { useEffect, useMemo, useCallback, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Descriptions,
  Select,
  message,
  Spin,
  Empty,
} from 'antd'
import {
  ReloadOutlined,
  ArrowLeftOutlined,
  BarChartOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import { keywordApi, trendApi } from '@/api/client'
import { CATEGORY_LABELS, CATEGORY_COLORS, type KeywordWithItems, type KeywordTrend, type ItemLite } from '@/types'
import type { ColumnType } from 'antd/es/table'

// 安全的分类标签获取函数
const getCategoryLabel = (category: string | null | undefined): string => {
  if (!category) return '未分类'
  if (category in CATEGORY_LABELS) {
    return CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]
  }
  return '未分类'
}

// 时间范围选项
const TIME_RANGE_OPTIONS = [
  { label: '7天', value: 7 },
  { label: '14天', value: 14 },
  { label: '30天', value: 30 },
  { label: '60天', value: 60 },
  { label: '90天', value: 90 },
]

// 常量
const DEFAULT_ITEMS_LIMIT = 50
const DEFAULT_TREND_DAYS = 30

export default function KeywordDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // 状态管理
  const [keyword, setKeyword] = useState<KeywordWithItems | null>(null)
  const [trendData, setTrendData] = useState<KeywordTrend | null>(null)
  const [loading, setLoading] = useState(true)
  const [trendLoading, setTrendLoading] = useState(false)
  const [days, setDays] = useState(30)

  const keywordId = id ? parseInt(id, 10) : null

  // 验证 keywordId 是否有效
  const isValidKeywordId = keywordId !== null && !isNaN(keywordId)

  // 加载关键词详情
  const loadKeywordDetail = useCallback(async () => {
    if (!isValidKeywordId) return

    try {
      setLoading(true)
      const data = await keywordApi.getDetail(keywordId, DEFAULT_ITEMS_LIMIT)
      setKeyword(data)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      message.error(`加载关键词详情失败: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }, [keywordId, isValidKeywordId])

  // 加载趋势数据
  const loadTrendData = useCallback(async (days: number) => {
    if (!isValidKeywordId) return

    try {
      setTrendLoading(true)
      const data = await trendApi.getKeywordTrend(keywordId, days)
      setTrendData(data)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      message.error(`加载趋势数据失败: ${errorMessage}`)
    } finally {
      setTrendLoading(false)
    }
  }, [keywordId, isValidKeywordId])

  // 刷新数据
  const handleRefresh = useCallback(async () => {
    await Promise.all([
      loadKeywordDetail(),
      loadTrendData(days),
    ])
  }, [loadKeywordDetail, loadTrendData, days])

  // 处理时间范围变化
  const handleDaysChange = useCallback((newDays: number) => {
    setDays(newDays)
    loadTrendData(newDays)
  }, [loadTrendData])

  // 初始化
  useEffect(() => {
    if (isValidKeywordId) {
      loadKeywordDetail()
      loadTrendData(DEFAULT_TREND_DAYS)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keywordId]) // 只依赖 keywordId，避免循环依赖

  // ECharts 趋势图配置
  const trendChartOption = useMemo(() => {
    if (!trendData || trendData.trends.length === 0) {
      return null
    }

    const dates = trendData.trends.map((t) => t.date)
    const counts = trendData.trends.map((t) => t.count)
    const avgScores = trendData.trends.map((t) => t.avg_score || 0)

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['出现次数', '平均热度'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          rotate: 45,
          interval: Math.ceil(dates.length / 10) - 1,
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '出现次数',
          position: 'left',
        },
        {
          type: 'value',
          name: '平均热度',
          position: 'right',
        },
      ],
      series: [
        {
          name: '出现次数',
          type: 'line',
          yAxisIndex: 0,
          data: counts,
          smooth: true,
          itemStyle: {
            color: '#1890ff',
          },
          areaStyle: {
            opacity: 0.2,
          },
        },
        {
          name: '平均热度',
          type: 'line',
          yAxisIndex: 1,
          data: avgScores,
          smooth: true,
          itemStyle: {
            color: '#52c41a',
          },
        },
      ],
    }
  }, [trendData])

  // 内容表格列配置
  const itemColumns: ColumnType<ItemLite>[] = useMemo(() => [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: unknown, __: ItemLite, index: number) => index + 1,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (title: string, record: ItemLite) => (
        <a
          href={record.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ textDecoration: 'none' }}
        >
          {title}
        </a>
      ),
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 80,
      render: (platform: string) => {
        const platformConfig: Record<string, { label: string; color: string }> = {
          zhihu: { label: '知乎', color: 'blue' },
          bilibili: { label: 'B站', color: 'cyan' },
        }
        const config = platformConfig[platform] || { label: platform, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      },
    },
    {
      title: '热度',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      sorter: (a: ItemLite, b: ItemLite) => a.score - b.score,
      defaultSortOrder: 'descend' as const,
      render: (score: number) => score.toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: ItemLite) => (
        <Button
          type="link"
          size="small"
          icon={<LinkOutlined />}
          href={record.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`打开${record.title}`}
        />
      ),
    },
  ], [])

  // 加载状态
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    )
  }

  // 关键词不存在
  if (!keyword) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Empty description="关键词不存在" />
        <Button type="primary" onClick={() => navigate(-1)}>
          返回
        </Button>
      </div>
    )
  }

  const categoryLabel = getCategoryLabel(keyword.category)
  const categoryColor = CATEGORY_COLORS[keyword.category || 'OTHER'] ?? '#8c8c8c'

  return (
    <div>
      {/* 头部操作栏 */}
      <Space style={{ marginBottom: 16 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(-1)}
          aria-label="返回上一页"
        >
          返回
        </Button>
        <h2>关键词详情</h2>
        <Button
          icon={<ReloadOutlined />}
          loading={loading || trendLoading}
          onClick={handleRefresh}
          aria-label="刷新数据"
        >
          刷新
        </Button>
      </Space>

      {/* 关键词基本信息 */}
      <Card style={{ marginBottom: 16 }}>
        <Descriptions
          title={keyword.word}
          column={3}
          items={[
            {
              label: '分类',
              children: (
                <Tag color={categoryColor} style={{ fontSize: '14px' }}>
                  {categoryLabel}
                </Tag>
              ),
            },
            {
              label: '出现次数',
              children: <Statistic value={keyword.count} valueStyle={{ fontSize: '18px' }} />,
            },
            {
              label: '关联内容',
              children: <Statistic value={keyword.items.length} valueStyle={{ fontSize: '18px' }} />,
            },
            {
              label: '首次出现',
              children: dayjs(keyword.first_seen).format('YYYY-MM-DD'),
            },
            {
              label: '最后出现',
              children: dayjs(keyword.last_seen).format('YYYY-MM-DD'),
            },
            {
              label: '活跃天数',
              children: dayjs(keyword.last_seen).diff(dayjs(keyword.first_seen), 'day') + 1,
            },
          ]}
        />
      </Card>

      {/* 趋势图表 */}
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <span>趋势分析</span>
            <Select
              value={days}
              onChange={handleDaysChange}
              options={TIME_RANGE_OPTIONS}
              style={{ width: 100 }}
              size="small"
            />
            {trendData && (
              <Tag color="blue">最近 {trendData.trends.length} 天有数据</Tag>
            )}
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {trendLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin />
          </div>
        ) : trendChartOption ? (
          <ReactECharts
            option={trendChartOption}
            style={{ height: 350 }}
            opts={{ renderer: 'svg' }}
          />
        ) : (
          <Empty description="暂无趋势数据" />
        )}
      </Card>

      {/* 关联内容列表 */}
      <Card
        title={
          <Space>
            <LinkOutlined />
            <span>关联内容</span>
            <Tag>共 {keyword.items.length} 条</Tag>
          </Space>
        }
      >
        {keyword.items.length > 0 ? (
          <Table
            columns={itemColumns}
            dataSource={keyword.items}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            size="small"
          />
        ) : (
          <Empty description="暂无关联内容" />
        )}
      </Card>
    </div>
  )
}
