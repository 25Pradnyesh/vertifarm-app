import React from 'react';
import { View, StyleSheet, Dimensions, Text } from 'react-native';
import Svg, { Path, Line, Circle, Text as SvgText } from 'react-native-svg';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';

export interface MetricSeries {
  id: string;
  name: string;
  color: string;
  data: number[]; // 0-100 normalized or scaled
  visible?: boolean;
}

interface MultiMetricChartProps {
  series: MetricSeries[];
  timestamps?: string[];
  height?: number;
  width?: number;
}

const { width: screenWidth } = Dimensions.get('window');

export function MultiMetricChart({
  series = [],
  timestamps = ['00:00', '06:00', '12:00', '18:00', '24:00'],
  height = 220,
  width = screenWidth - 48,
}: MultiMetricChartProps) {
  const paddingLeft = 32;
  const paddingRight = 16;
  const paddingTop = 16;
  const paddingBottom = 28;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const yTicks = [100, 80, 60, 40, 20, 0];

  return (
    <View style={[styles.container, { width }]}>
      <Svg width={width} height={height}>
        {/* Horizontal grid lines & Y-Axis labels */}
        {yTicks.map((val) => {
          const yPos = paddingTop + (1 - val / 100) * chartHeight;
          return (
            <React.Fragment key={`ytick-${val}`}>
              <Line
                x1={paddingLeft}
                y1={yPos}
                x2={width - paddingRight}
                y2={yPos}
                stroke={colors.border}
                strokeWidth="1"
                strokeDasharray="4, 4"
              />
              <SvgText
                x={paddingLeft - 8}
                y={yPos + 4}
                fontSize="10"
                fill={colors.textMuted}
                textAnchor="end"
                fontWeight="500"
              >
                {val}
              </SvgText>
            </React.Fragment>
          );
        })}

        {/* X-Axis timestamps */}
        {timestamps.map((time, idx) => {
          const xPos = paddingLeft + (idx / (timestamps.length - 1 || 1)) * chartWidth;
          return (
            <SvgText
              key={`x-label-${idx}`}
              x={xPos}
              y={height - 8}
              fontSize="9"
              fill={colors.textMuted}
              textAnchor="middle"
              fontWeight="500"
            >
              {time}
            </SvgText>
          );
        })}

        {/* Metric Series Lines & Dots */}
        {series
          .filter((s) => s.visible !== false)
          .map((s) => {
            const points = s.data.map((val, idx) => {
              const clamped = Math.max(0, Math.min(100, val));
              const x = paddingLeft + (idx / (s.data.length - 1 || 1)) * chartWidth;
              const y = paddingTop + (1 - clamped / 100) * chartHeight;
              return { x, y };
            });

            const pathD = points.reduce((acc, curr, index) => {
              return index === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`;
            }, '');

            return (
              <React.Fragment key={`series-${s.id}`}>
                <Path
                  d={pathD}
                  stroke={s.color}
                  strokeWidth="2.5"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {points.map((p, pIdx) => (
                  <Circle
                    key={`dot-${s.id}-${pIdx}`}
                    cx={p.x}
                    cy={p.y}
                    r="3.5"
                    fill={colors.surface}
                    stroke={s.color}
                    strokeWidth="2"
                  />
                ))}
              </React.Fragment>
            );
          })}
      </Svg>

      {/* Legend below chart */}
      <View style={styles.legendContainer}>
        {series.map((s) => (
          <View key={`legend-${s.id}`} style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: s.color }]} />
            <Text style={styles.legendLabel}>{s.name}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  legendContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginTop: spacing.sm,
    justifyContent: 'center',
    paddingHorizontal: spacing.sm,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendLabel: {
    fontSize: 12,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
});
