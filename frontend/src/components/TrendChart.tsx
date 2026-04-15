/**
 * 趋势图表组件 - 使用 ECharts 显示关键词趋势
 */
import { useMemo, useRef } from 'react';
import { memo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import dayjs from 'dayjs';

// 常量定义
const MAX_SERIES_DISPLAY = 5;
const MAX_SERIES_THRESHOLD = 10;

// ECharts Tooltip 参数类型定义
interface TooltipParam {
  axisValue: string;
  seriesName: string;
  value: number;
  color?: string;
  [key: string]: unknown;
}

export interface TrendDataPoint {
  date: string;
  count: number;
  avg_score: number | null;
}

export interface TrendChartData {
  keyword: string;
  keyword_id: number;
  category: string | null;
  trends: TrendDataPoint[];
}

interface TrendChartProps {
  data: TrendChartData[];
  height?: number | string;
  title?: string;
  showAvgScore?: boolean;
}

/**
 * 将趋势数据转换为 ECharts 格式
 */
function convertToEChartsFormat(data: TrendChartData[], showAvgScore: boolean) {
  // 提取所有日期并排序
  const allDates = new Set<string>();
  data.forEach((item) => {
    item.trends.forEach((point) => {
      allDates.add(point.date);
    });
  });

  const dates = Array.from(allDates).sort();

  // 为每个关键词构建系列数据
  const series = data.map((item) => {
    const counts = dates.map((date) => {
      const point = item.trends.find((p) => p.date === date);
      return point?.count ?? 0;
    });

    const avgScores = showAvgScore
      ? dates.map((date) => {
          const point = item.trends.find((p) => p.date === date);
          return point?.avg_score ?? 0;
        })
      : [];

    return {
      name: item.keyword,
      counts,
      avgScores,
    };
  });

  // 获取前N个和后N个系列（如果数据太多）
  let selectedSeries = series;
  if (series.length > MAX_SERIES_THRESHOLD) {
    selectedSeries = [...series.slice(0, MAX_SERIES_DISPLAY), ...series.slice(-MAX_SERIES_DISPLAY)];
  }

  return { dates, series: selectedSeries };
}

/**
 * 趋势图表组件 - 使用 memo 防止不必要的重渲染
 */
const TrendChart = memo(function TrendChart({
  data,
  height = 400,
  title,
  showAvgScore = false,
}: TrendChartProps) {
  const chartRef = useRef<ReactECharts>(null);

  // 处理空数据
  if (!data || data.length === 0) {
    return (
      <div
        style={{
          height: typeof height === 'number' ? `${height}px` : height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
        }}
      >
        暂无趋势数据
      </div>
    );
  }

  // Memoize 数据转换
  const { dates, series } = useMemo(
    () => convertToEChartsFormat(data, showAvgScore),
    [data, showAvgScore]
  );

  // Memoize 图例数据
  const legendData = useMemo(() => series.map((s) => s.name), [series]);

  // Memoize 系列配置
  const seriesConfig = useMemo(() => {
    return series.flatMap((item) => {
      const configs: EChartsOption['series'] = [
        {
          name: item.name,
          type: 'line',
          data: item.counts,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2 },
          emphasis: { focus: 'series' },
        },
      ];

      if (showAvgScore) {
        configs.push({
          name: `${item.name}(平均热度)`,
          type: 'line',
          data: item.avgScores,
          smooth: true,
          symbol: 'diamond',
          symbolSize: 4,
          lineStyle: { type: 'dashed', width: 1 },
          emphasis: { focus: 'series' },
        });
      }

      return configs;
    });
  }, [series, showAvgScore]);

  // Memoize 图表配置
  const option: EChartsOption = useMemo(() => {
    return {
      title: title
        ? {
            text: title,
            left: 'center',
            textStyle: { fontSize: 16, fontWeight: 600 },
          }
        : undefined,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: unknown) => {
          const typedParams = params as TooltipParam[];
          if (!Array.isArray(typedParams) || typedParams.length === 0) return '';

          const date = typedParams[0]?.axisValue;
          if (!date) return '';

          let result = `<strong>${dayjs(date).format('YYYY-MM-DD')}</strong><br/>`;

          // 按系列分组显示
          const grouped = new Map<string, TooltipParam[]>();
          typedParams.forEach((p) => {
            const baseName = p.seriesName.replace('(平均热度)', '');
            if (!grouped.has(baseName)) {
              grouped.set(baseName, []);
            }
            grouped.get(baseName)!.push(p);
          });

          grouped.forEach((items, keyword) => {
            result += `<br/><strong>${keyword}</strong>`;
            items.forEach((p) => {
              const isAvgScore = p.seriesName.includes('(平均热度)');
              const label = isAvgScore ? '平均热度' : '出现次数';
              result += `<br/>　　${label}: ${p.value.toLocaleString()}`;
            });
          });

          return result;
        },
      },
      legend: {
        data: legendData,
        top: title ? 50 : 10,
        type: 'scroll',
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: title ? 100 : 80,
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          formatter: (value: string) => dayjs(value).format('MM-DD'),
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '出现次数',
          position: 'left',
          axisLine: { show: true, lineStyle: { color: '#5470c6' } },
          axisLabel: { formatter: '{value}' },
        },
        showAvgScore
          ? {
              type: 'value',
              name: '平均热度',
              position: 'right',
              axisLine: { show: true, lineStyle: { color: '#91cc75' } },
              axisLabel: { formatter: '{value}' },
              splitLine: { show: false },
            }
          : undefined,
      ].filter(Boolean),
      series: seriesConfig,
      dataZoom: dates.length > 30
        ? [
            {
              type: 'inside',
              start: 0,
              end: 100,
            },
            {
              start: 0,
              end: 100,
            },
          ]
        : undefined,
    };
  }, [dates, seriesConfig, legendData, title, showAvgScore]);

  return (
    <div role="img" aria-label={`趋势图表: ${title || '关键词趋势'}`}>
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
});

export default TrendChart;

/**
 * 简单趋势图 - 单个关键词的趋势
 */
interface SimpleTrendChartProps {
  data: TrendDataPoint[];
  keyword: string;
  height?: number | string;
}

export const SimpleTrendChart = memo(function SimpleTrendChart({
  data,
  keyword,
  height = 200,
}: SimpleTrendChartProps) {
  // 处理空数据
  if (!data || data.length === 0) {
    return (
      <div
        style={{
          height: typeof height === 'number' ? `${height}px` : height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#999',
        }}
      >
        暂无趋势数据
      </div>
    );
  }

  const dates = useMemo(() => data.map((d) => d.date), [data]);
  const counts = useMemo(() => data.map((d) => d.count), [data]);

  const option: EChartsOption = useMemo(
    () => ({
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: {
          formatter: (value: string) => dayjs(value).format('MM-DD'),
        },
      },
      yAxis: {
        type: 'value',
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: unknown) => {
          const typedParams = params as TooltipParam[];
          if (!Array.isArray(typedParams) || typedParams.length === 0) return '';

          const p = typedParams[0];
          const point = data.find((d) => d.date === p.axisValue);
          return `${dayjs(p.axisValue).format('YYYY-MM-DD')}<br/>
                  出现次数: ${p.value}<br/>
                  ${point?.avg_score ? `平均热度: ${point.avg_score.toFixed(1)}` : ''}`;
        },
      },
      series: [
        {
          data: counts,
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.3 },
          lineStyle: { width: 2 },
        },
      ],
    }),
    [dates, counts, data]
  );

  return (
    <div role="img" aria-label={`${keyword} 趋势图`}>
      <ReactECharts
        option={option}
        style={{ height: typeof height === 'number' ? `${height}px` : height }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
});
