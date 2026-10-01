import React from 'react';
import { View, StyleSheet, Dimensions, Text } from 'react-native';
import Svg, { Path, Line, Circle, Text as SvgText, Defs, LinearGradient, Stop } from 'react-native-svg';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';

interface SingleMetricChartProps {
  data: number[];
  timestamps?: string[];
  color?: string;
  height?: number;
  width?: number;
  unit?: string;
}

const { width: screenWidth } = Dimensions.get('window');

export function SingleMetricChart({
  data = [],
  timestamps = [],
  color = colors.leafGreen,
  height = 190,
  width = screenWidth - 64,
  unit = '',
}: SingleMetricChartProps) {
  if (!data || data.length === 0) {
    return (
      <View style={[styles.container, { height, width }]}>
        <Text style={styles.noDataText}>No telemetry data available</Text>
      </View>
    );
  }

  const paddingLeft = 32;
  const paddingRight = 16;
  const paddingTop = 18;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const rawMin = Math.min(...data);
  const rawMax = Math.max(...data);
  const spread = rawMax - rawMin || 1;
  const yMin = Math.max(0, Math.floor(rawMin - spread * 0.15));
  const yMax = Math.ceil(rawMax + spread * 0.15);
  const yRange = yMax - yMin || 1;

  // Generate 3 Y-axis grid levels
  const yTicks = [yMin, Math.round((yMin + yMax) / 2), yMax];

  // Coordinates calculation
  const points = data.map((val, index) => {
    const x = paddingLeft + (index / (data.length - 1 || 1)) * chartWidth;
    const y = paddingTop + (1 - (val - yMin) / yRange) * chartHeight;
    return { x, y, val };
  });

  // Construct SVG line path
  const pathD = points.reduce((acc, curr, index) => {
    return index === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`;
  }, '');

  // Fill area under curve
  const areaD = `${pathD} L ${points[points.length - 1].x} ${paddingTop + chartHeight} L ${points[0].x} ${paddingTop + chartHeight} Z`;

  // Filter X-axis labels to max 6 labels for clean display
  const step = Math.max(1, Math.floor(timestamps.length / 5));
  const displayTimestamps = timestamps.filter((_, i) => i % step === 0 || i === timestamps.length - 1);

  return (
    <View style={[styles.container, { height, width }]}>
      <Svg width={width} height={height}>
        <Defs>
          <LinearGradient id="gradientArea" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0%" stopColor={color} stopOpacity="0.25" />
            <Stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </LinearGradient>
        </Defs>

        {/* Horizontal grid lines and Y-axis tick labels */}
        {yTicks.map((tick, index) => {
          const yPos = paddingTop + (1 - (tick - yMin) / yRange) * chartHeight;
          return (
            <React.Fragment key={`grid-${index}`}>
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
                {tick}
              </SvgText>
            </React.Fragment>
          );
        })}

        {/* Gradient Fill under line */}
        <Path d={areaD} fill="url(#gradientArea)" />

        {/* Line graph */}
        <Path d={pathD} stroke={color} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />

        {/* Circular markers at each point */}
        {points.map((p, idx) => (
          <Circle
            key={`point-${idx}`}
            cx={p.x}
            cy={p.y}
            r={idx === points.length - 1 ? 5 : 3.5}
            fill={colors.surface}
            stroke={color}
            strokeWidth="2"
          />
        ))}

        {/* X-axis tick timestamps */}
        {displayTimestamps.map((time, idx) => {
          const origIdx = timestamps.indexOf(time);
          const x = paddingLeft + (origIdx / (timestamps.length - 1 || 1)) * chartWidth;
          return (
            <SvgText
              key={`time-${idx}`}
              x={x}
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
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  noDataText: {
    color: colors.textMuted,
    fontSize: typography.fontSize.caption,
  },
});
