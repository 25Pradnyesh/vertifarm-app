import React, { ReactNode } from 'react';
import { View, StyleSheet, ScrollView, ViewStyle, StyleProp } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../../constants/colors';
import { spacing } from '../../constants/spacing';

interface ScreenContainerProps {
  children: ReactNode;
  scroll?: boolean;
  padding?: boolean;
  backgroundColor?: string;
  edges?: ('top' | 'bottom' | 'left' | 'right')[];
  style?: StyleProp<ViewStyle>;
}

export function ScreenContainer({
  children,
  scroll = true,
  padding = true,
  backgroundColor = colors.background,
  edges = ['top', 'bottom'],
  style,
}: ScreenContainerProps) {
  const containerStyle: ViewStyle = {
    flex: 1,
    backgroundColor,
  };

  const contentStyles: StyleProp<ViewStyle> = [
    padding && { paddingHorizontal: spacing.screenPadding },
    style,
  ];

  return (
    <SafeAreaView style={containerStyle} edges={edges}>
      {scroll ? (
        <ScrollView
          style={{ flex: 1 }}
          contentContainerStyle={contentStyles}
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[{ flex: 1 }, contentStyles]}>{children}</View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({});

