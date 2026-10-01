import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { ScreenContainer } from '../../components/ui/ScreenContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { colors } from '../../constants/colors';
import { typography } from '../../constants/typography';
import { spacing } from '../../constants/spacing';
import { radii } from '../../constants/radii';

const SENSOR_MODELS = [
  { id: 'DHT22', name: 'DHT22', metric: 'Temperature & Humidity', icon: 'thermometer-outline' },
  { id: 'Capacitive', name: 'Capacitive v1.2', metric: 'Soil Moisture', icon: 'water-outline' },
  { id: 'Analog-pH', name: 'Analog Probe', metric: 'Soil pH', icon: 'flask-outline' },
  { id: 'Analog-TDS', name: 'Analog TDS Sensor', metric: 'TDS / Nutrients', icon: 'speedometer-outline' },
  { id: 'BH1750', name: 'BH1750 Ambient', metric: 'Light Lux', icon: 'sunny-outline' },
  { id: 'ESP32-CAM', name: 'ESP32-CAM', metric: 'Plant Monitoring', icon: 'camera-outline' },
];

const ZONES = ['Zone 1 (Tomatoes)', 'Zone 2 (Lettuce)', 'Zone 3 (Microgreens)'];

export default function AddSensorScreen() {
  const router = useRouter();
  const [selectedModel, setSelectedModel] = useState('DHT22');
  const [sensorName, setSensorName] = useState('Greenhouse 1 - Canopy Sensor');
  const [selectedZone, setSelectedZone] = useState('Zone 1 (Tomatoes)');
  const [pollingRate, setPollingRate] = useState('5s');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSaveSensor = async () => {
    if (!sensorName.trim()) {
      Alert.alert('Missing Field', 'Please enter a name for the sensor.');
      return;
    }

    setIsSubmitting(true);
    await new Promise((resolve) => setTimeout(resolve, 600));
    setIsSubmitting(false);

    Alert.alert(
      'Sensor Paired Successfully',
      `Device "${sensorName}" has been registered to ${selectedZone}. Telemetry will start syncing.`,
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  return (
    <ScreenContainer scroll={true} padding={true}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.title}>Add Sensor</Text>
        <View style={{ width: 24 }} />
      </View>

      <Text style={styles.sectionSubtitle}>
        Select hardware model and assign to a vertical farming zone.
      </Text>

      {/* Sensor Hardware Type Grid */}
      <Text style={styles.fieldLabel}>Hardware Model</Text>
      <View style={styles.modelGrid}>
        {SENSOR_MODELS.map((item) => {
          const isSelected = selectedModel === item.id;
          return (
            <TouchableOpacity
              key={item.id}
              style={[styles.modelCard, isSelected && styles.modelCardActive]}
              onPress={() => setSelectedModel(item.id)}
              activeOpacity={0.7}
            >
              <View
                style={[
                  styles.modelIconCircle,
                  isSelected && styles.modelIconCircleActive,
                ]}
              >
                <Ionicons
                  name={item.icon as any}
                  size={20}
                  color={isSelected ? colors.primary : colors.textSecondary}
                />
              </View>
              <Text style={[styles.modelName, isSelected && styles.modelNameActive]}>
                {item.name}
              </Text>
              <Text style={styles.modelMetric}>{item.metric}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Sensor Name Input */}
      <View style={styles.inputGroup}>
        <Text style={styles.fieldLabel}>Sensor Display Name</Text>
        <View style={styles.inputWrapper}>
          <Ionicons name="hardware-chip-outline" size={20} color={colors.textSecondary} />
          <TextInput
            style={styles.input}
            value={sensorName}
            onChangeText={setSensorName}
            placeholder="e.g. Canopy Temperature DHT22"
            placeholderTextColor={colors.textMuted}
          />
        </View>
      </View>

      {/* Target Zone Selection */}
      <View style={styles.inputGroup}>
        <Text style={styles.fieldLabel}>Target Zone</Text>
        <View style={styles.chipRow}>
          {ZONES.map((zone) => {
            const isSelected = selectedZone === zone;
            return (
              <TouchableOpacity
                key={zone}
                style={[styles.chip, isSelected && styles.chipActive]}
                onPress={() => setSelectedZone(zone)}
                activeOpacity={0.7}
              >
                <Text style={[styles.chipText, isSelected && styles.chipTextActive]}>
                  {zone}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Sampling Frequency */}
      <View style={styles.inputGroup}>
        <Text style={styles.fieldLabel}>Sampling Frequency</Text>
        <View style={styles.frequencyRow}>
          {['1s', '5s', '15s', '30s', '60s'].map((freq) => {
            const isSelected = pollingRate === freq;
            return (
              <TouchableOpacity
                key={freq}
                style={[styles.freqPill, isSelected && styles.freqPillActive]}
                onPress={() => setPollingRate(freq)}
                activeOpacity={0.7}
              >
                <Text style={[styles.freqText, isSelected && styles.freqTextActive]}>
                  {freq}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Submit Button */}
      <View style={styles.submitContainer}>
        <Button
          title="Pair & Save Sensor"
          onPress={handleSaveSensor}
          variant="primary"
          fullWidth
          loading={isSubmitting}
        />
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  backButton: {
    padding: spacing.xs,
  },
  title: {
    fontSize: typography.fontSize.navTitle,
    fontWeight: typography.fontWeight.bold,
    color: colors.textPrimary,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },
  fieldLabel: {
    fontSize: 14,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  modelGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  modelCard: {
    width: '48%',
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radii.card,
    padding: spacing.md,
    alignItems: 'flex-start',
  },
  modelCardActive: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceSubtle,
  },
  modelIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  modelIconCircleActive: {
    backgroundColor: colors.primaryMuted,
  },
  modelName: {
    fontSize: 13,
    fontWeight: typography.fontWeight.semibold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  modelNameActive: {
    color: colors.primary,
  },
  modelMetric: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  inputGroup: {
    marginBottom: spacing.lg,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radii.input,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  input: {
    flex: 1,
    marginLeft: spacing.sm,
    fontSize: typography.fontSize.input,
    color: colors.textPrimary,
  },
  chipRow: {
    flexDirection: 'column',
    gap: spacing.xs,
  },
  chip: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radii.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipActive: {
    backgroundColor: colors.primaryMuted,
    borderColor: colors.primary,
  },
  chipText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: typography.fontWeight.medium,
  },
  chipTextActive: {
    color: colors.primary,
    fontWeight: typography.fontWeight.semibold,
  },
  frequencyRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  freqPill: {
    flex: 1,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  freqPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  freqText: {
    fontSize: 13,
    fontWeight: typography.fontWeight.medium,
    color: colors.textSecondary,
  },
  freqTextActive: {
    color: colors.textInverse,
    fontWeight: typography.fontWeight.semibold,
  },
  submitContainer: {
    marginTop: spacing.md,
    marginBottom: spacing.xxl,
  },
});
