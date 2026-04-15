/**
 * 分类浏览页面
 */
import { useEffect, useMemo, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Space,
  Tabs,
  message,
  Progress,
} from 'antd'
import { ReloadOutlined, BarChartOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { useKeywordStore } from '@/store/useStore'
import { CATEGORY_LABELS, CATEGORY_COLORS, type Keyword } from '@/types'
import type { ColumnType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'

// 安全的分类标签获取函数
const getCategoryLabel = (category: string | null): string => {
  if (!category) return '未分类'
  if (category in CATEGORY_LABELS) {
    return CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS]
  }
  return '未分类'
}

interface CategoryData {
  category: string | null
  count: number
  percentage: number
  keywords: Keyword[]
}

export default function Categories() {
  const navigate = useNavigate()

  // 使用选择器优化订阅
  const { keywords, loading, refreshKeywords } = useKeywordStore((state) => ({
    keywords: state.keywords,
    loading: state.loading,
    refreshKeywords: state.refreshKeywords,
  }))

  // 刷新数据的处理函数
  const handleRefresh = useCallback(async () => {
    try {
      await refreshKeywords({ limit: 500 })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      message.error(`加载关键词失败: ${errorMessage}`)
    }
  }, [refreshKeywords])

  // 按分类组织数据
  const categoriesData = useMemo<CategoryData[]>(() => {
    const total = keywords.length
    const categoryMap = new Map<string | null, Keyword[]>()

    // 初始化所有分类
    Object.keys(CATEGORY_LABELS).forEach((cat) => categoryMap.set(cat, []))
    categoryMap.set(null, []) // 未分类

    // 分组关键词
    keywords.forEach((keyword) => {
      const cat = keyword.category || null
      if (!categoryMap.has(cat)) {
        categoryMap.set(cat, [])
      }
      categoryMap.get(cat)!.push(keyword)
    })

    // 转换为数组并计算百分比
    return Array.from(categoryMap.entries())
      .filter(([_, kws]) => kws.length > 0) // 只有关键词的分类才显示
      .map(([category, kws]) => ({
        category,
        count: kws.length,
        percentage: total > 0 ? Math.round((kws.length / total) * 100) : 0,
        keywords: kws.sort((a, b) => b.count - a.count), // 按出现次数排序
      }))
      .sort((a, b) => b.count - a.count) // 按数量排序
  }, [keywords])

  // ECharts 饼图配置
  const pieChartOption = useMemo(() => {
    const data = categoriesData
      .filter((cat) => cat.category) // 排除未分类
      .map((cat) => ({
        name: getCategoryLabel(cat.category),
        value: cat.count,
        itemStyle: {
          color: CATEGORY_COLORS[cat.category || ''] || '#8c8c8c',
        },
      }))

    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        data: data.map((d) => d.name),
      },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{d}%',
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 16,
              fontWeight: 'bold',
            },
          },
          data,
        },
      ],
    }
  }, [categoriesData])

  // ECharts 柱状图配置
  const barChartOption = useMemo(() => {
    const sortedData = [...categoriesData]
      .filter((cat) => cat.category)
      .sort((a, b) => b.count - a.count)

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
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
        data: sortedData.map((cat) => getCategoryLabel(cat.category)),
        axisLabel: {
          rotate: 0,
          interval: 0,
        },
      },
      yAxis: {
        type: 'value',
      },
      series: [
        {
          type: 'bar',
          data: sortedData.map((cat) => ({
            value: cat.count,
            itemStyle: {
              color: CATEGORY_COLORS[cat.category || ''] || '#8c8c8c',
            },
          })),
          barWidth: '60%',
          label: {
            show: true,
            position: 'top',
          },
        },
      ],
    }
  }, [categoriesData])

  // 表格列配置
  const columns: ColumnType<Keyword>[] = useMemo(() => [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      render: (_: unknown, __: Keyword, index: number) => index + 1,
    },
    {
      title: '关键词',
      dataIndex: 'word',
      key: 'word',
      width: 150,
      render: (word: string, record: Keyword) => (
        <Button
          type="link"
          style={{ padding: 0, height: 'auto' }}
          onClick={() => navigate(`/keyword/${record.id}`)}
        >
          {word}
        </Button>
      ),
    },
    {
      title: '出现次数',
      dataIndex: 'count',
      key: 'count',
      width: 100,
      sorter: (a: Keyword, b: Keyword) => a.count - b.count,
      defaultSortOrder: 'descend',
    },
    {
      title: '最后出现',
      dataIndex: 'last_seen',
      key: 'last_seen',
      width: 120,
      render: (date: string) => date,
    },
  ], [navigate])

  // Tab items
  const tabItems = useMemo(() => {
    return categoriesData.map((catData) => {
      const categoryKey = catData.category || 'OTHER'
      return {
        key: categoryKey,
        label: (
          <Space>
            <span>{getCategoryLabel(catData.category)}</span>
            <Tag color={CATEGORY_COLORS[categoryKey]}>{catData.count}</Tag>
          </Space>
        ),
        children: (
          <Table
            columns={columns}
            dataSource={catData.keywords}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            size="small"
          />
        ),
      }
    })
  }, [categoriesData, columns, loading])

  // 初始化
  useEffect(() => {
    let mounted = true

    const initializeData = async () => {
      try {
        await refreshKeywords({ limit: 500 })
      } catch (error) {
        if (mounted) {
          message.error('加载关键词失败')
        }
      }
    }

    initializeData()

    return () => {
      mounted = false
    }
  }, [refreshKeywords])

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <h2>分类浏览</h2>
        <Button
          icon={<ReloadOutlined />}
          loading={loading}
          onClick={handleRefresh}
          aria-label="刷新数据"
        >
          刷新
        </Button>
      </Space>

      {/* 分类概览卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {categoriesData.map((catData) => {
          const categoryKey = catData.category || 'OTHER'
          return (
            <Col span={3} key={categoryKey}>
              <Card
                size="small"
                style={{
                  borderColor: CATEGORY_COLORS[categoryKey],
                  backgroundColor: `${CATEGORY_COLORS[categoryKey]}08`,
                }}
              >
                <Statistic
                  title={getCategoryLabel(catData.category)}
                  value={catData.count}
                  suffix={`(${catData.percentage}%)`}
                  valueStyle={{
                    color: CATEGORY_COLORS[categoryKey],
                    fontSize: '18px',
                    fontWeight: 'bold',
                  }}
                />
                <Progress
                  percent={catData.percentage}
                  strokeColor={CATEGORY_COLORS[categoryKey]}
                  showInfo={false}
                  size="small"
                  style={{ marginTop: 8 }}
                />
              </Card>
            </Col>
          )
        })}
      </Row>

      <Row gutter={16}>
        {/* 分类分布饼图 */}
        <Col span={12}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                <span>分类分布</span>
              </Space>
            }
          >
            {categoriesData.length > 0 ? (
              <ReactECharts
                option={pieChartOption}
                style={{ height: 350 }}
                opts={{ renderer: 'svg' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                暂无数据
              </div>
            )}
          </Card>
        </Col>

        {/* 分类统计柱状图 */}
        <Col span={12}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                <span>分类数量对比</span>
              </Space>
            }
          >
            {categoriesData.length > 0 ? (
              <ReactECharts
                option={barChartOption}
                style={{ height: 350 }}
                opts={{ renderer: 'svg' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                暂无数据
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 按分类展示关键词列表 */}
      <Card title="各分类关键词" style={{ marginTop: 16 }}>
        <Tabs
          items={tabItems}
          size="small"
          tabBarStyle={{ marginBottom: 0 }}
        />
      </Card>
    </div>
  )
}
