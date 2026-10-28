/**
 * VertiFarm Smart Sensor Thresholds & Alert Lifecycle Verification Suite (Node.js)
 * Tests threshold evaluation, state lifecycle, deduplication,
 * recovery hysteresis, permission denial handling, and notification routing.
 */

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✅ PASS: ${message}`);
    passed++;
  } else {
    console.error(`  ❌ FAIL: ${message}`);
    failed++;
  }
}

// 1. Reusable Sensor Threshold Config matching constants/thresholds.ts
const SENSOR_THRESHOLDS = {
  temperature: {
    metric: 'temperature',
    name: 'Temperature',
    unit: '°C',
    physicalMin: -40.0,
    physicalMax: 100.0,
    optimalMin: 20.0,
    optimalMax: 30.0,
    warningMin: 15.0,
    warningMax: 35.0,
    hysteresis: 0.5,
  },
  humidity: {
    metric: 'humidity',
    name: 'Humidity',
    unit: '%',
    physicalMin: 0.0,
    physicalMax: 100.0,
    optimalMin: 60.0,
    optimalMax: 80.0,
    warningMin: 40.0,
    warningMax: 90.0,
    hysteresis: 1.0,
  },
  soilMoisture: {
    metric: 'soilMoisture',
    name: 'Soil Moisture',
    unit: '%',
    physicalMin: 0.0,
    physicalMax: 100.0,
    optimalMin: 40.0,
    optimalMax: 60.0,
    warningMin: 30.0,
    warningMax: 75.0,
    hysteresis: 1.0,
  },
  ph: {
    metric: 'ph',
    name: 'Soil pH',
    unit: 'pH',
    physicalMin: 0.0,
    physicalMax: 14.0,
    optimalMin: 6.0,
    optimalMax: 7.0,
    warningMin: 5.5,
    warningMax: 7.5,
    hysteresis: 0.1,
  },
  tds: {
    metric: 'tds',
    name: 'TDS',
    unit: 'ppm',
    physicalMin: 0.0,
    physicalMax: 5000.0,
    optimalMin: 500.0,
    optimalMax: 800.0,
    warningMin: 400.0,
    warningMax: 1000.0,
    hysteresis: 10.0,
  },
  light: {
    metric: 'light',
    name: 'Light Intensity',
    unit: 'Lux',
    physicalMin: 0.0,
    physicalMax: 150000.0,
    optimalMin: 1000.0,
    optimalMax: 2000.0,
    warningMin: 500.0,
    warningMax: 3000.0,
    hysteresis: 50.0,
  },
};

function formatMetricValue(metric, value) {
  if (metric === 'ph') return Number(value).toFixed(2);
  if (metric === 'tds' || metric === 'light') return Math.round(Number(value)).toLocaleString();
  return Number(value).toFixed(1);
}

function evaluateSensorThreshold(metric, value, activeViolationDirection = null) {
  const config = SENSOR_THRESHOLDS[metric];
  if (!config) {
    return { isValid: false, isViolation: false, status: 'offline' };
  }

  if (value === null || value === undefined || value === '') {
    return { isValid: false, isViolation: false, status: 'offline' };
  }

  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num) || !isFinite(num)) {
    return { isValid: false, isViolation: false, status: 'offline' };
  }

  if (num < config.physicalMin || num > config.physicalMax) {
    return { isValid: false, isViolation: false, status: 'offline' };
  }

  const formattedVal = `${formatMetricValue(metric, num)} ${config.unit}`;
  const optMinStr = formatMetricValue(metric, config.optimalMin);
  const optMaxStr = formatMetricValue(metric, config.optimalMax);

  // Hysteresis recovery
  if (activeViolationDirection === 'high') {
    const recoveryThreshold = config.optimalMax - config.hysteresis;
    if (num > recoveryThreshold) {
      const isCritical = num > config.warningMax;
      const severity = isCritical ? 'critical' : 'warning';
      return {
        isValid: true,
        status: severity,
        severity,
        statusLabel: isCritical ? 'Critical High' : 'High',
        isViolation: true,
        violationDirection: 'high',
        title: `${config.name} is High`,
        notificationBody: `High ${config.name.toLowerCase()} detected: ${formattedVal} — Normal range: ${optMinStr}–${optMaxStr} ${config.unit}`,
        currentValueFormatted: formattedVal,
        thresholdValueFormatted: `> ${optMaxStr} ${config.unit}`,
      };
    }
  } else if (activeViolationDirection === 'low') {
    const recoveryThreshold = config.optimalMin + config.hysteresis;
    if (num < recoveryThreshold) {
      const isCritical = num < config.warningMin;
      const severity = isCritical ? 'critical' : 'warning';
      return {
        isValid: true,
        status: severity,
        severity,
        statusLabel: isCritical ? 'Critical Low' : 'Low',
        isViolation: true,
        violationDirection: 'low',
        title: `${config.name} is Low`,
        notificationBody: `${config.name} too low: ${formattedVal} — Minimum: ${optMinStr} ${config.unit}`,
        currentValueFormatted: formattedVal,
        thresholdValueFormatted: `< ${optMinStr} ${config.unit}`,
      };
    }
  }

  if (num > config.warningMax) {
    return {
      isValid: true,
      status: 'critical',
      severity: 'critical',
      statusLabel: 'Critical High',
      isViolation: true,
      violationDirection: 'high',
      title: `${config.name} is Critical`,
      notificationBody: `${config.name} critical: ${formattedVal} — Maximum: ${optMaxStr} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `> ${optMaxStr} ${config.unit}`,
    };
  }

  if (num < config.warningMin) {
    return {
      isValid: true,
      status: 'critical',
      severity: 'critical',
      statusLabel: 'Critical Low',
      isViolation: true,
      violationDirection: 'low',
      title: `${config.name} is Critical`,
      notificationBody: `${config.name} critical: ${formattedVal} — Minimum: ${optMinStr} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `< ${optMinStr} ${config.unit}`,
    };
  }

  if (num > config.optimalMax) {
    return {
      isValid: true,
      status: 'warning',
      severity: 'warning',
      statusLabel: 'High',
      isViolation: true,
      violationDirection: 'high',
      title: `${config.name} is High`,
      notificationBody: `High ${config.name.toLowerCase()} detected: ${formattedVal} — Normal range: ${optMinStr}–${optMaxStr} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `> ${optMaxStr} ${config.unit}`,
    };
  }

  if (num < config.optimalMin) {
    return {
      isValid: true,
      status: 'warning',
      severity: 'warning',
      statusLabel: 'Low',
      isViolation: true,
      violationDirection: 'low',
      title: `${config.name} is Low`,
      notificationBody: `${config.name} too low: ${formattedVal} — Minimum: ${optMinStr} ${config.unit}`,
      currentValueFormatted: formattedVal,
      thresholdValueFormatted: `< ${optMinStr} ${config.unit}`,
    };
  }

  return {
    isValid: true,
    status: 'healthy',
    severity: 'info',
    statusLabel: 'Normal',
    isViolation: false,
    title: `${config.name} Normal`,
    notificationBody: '',
    currentValueFormatted: formattedVal,
    thresholdValueFormatted: `${optMinStr}–${optMaxStr} ${config.unit}`,
  };
}

// Mock Alert Monitor State Machine
class MockSensorAlertMonitor {
  constructor() {
    this.activeAlerts = new Map();
    this.notificationsSent = [];
  }

  reset() {
    this.activeAlerts.clear();
    this.notificationsSent = [];
  }

  async processReading(reading, permissionGranted = true) {
    const key = `${reading.farmId || 'farm-1'}:${reading.metric}`;
    const existing = this.activeAlerts.get(key);

    const evaluation = evaluateSensorThreshold(
      reading.metric,
      reading.value,
      existing ? existing.direction : null
    );

    if (!evaluation.isValid) return null;

    if (evaluation.isViolation) {
      if (existing) {
        // DEDUPLICATION: Suppress repeated notifications
        existing.alert.currentValue = evaluation.currentValueFormatted;
        return null;
      }

      // New Alert
      const alert = {
        id: `alert-${reading.metric}-${Date.now()}`,
        farmId: reading.farmId || 'farm-1',
        metric: reading.metric,
        severity: evaluation.severity,
        title: evaluation.title,
        description: evaluation.notificationBody,
        currentValue: evaluation.currentValueFormatted,
        thresholdValue: evaluation.thresholdValueFormatted,
        isResolved: false,
      };

      this.activeAlerts.set(key, {
        alert,
        direction: evaluation.violationDirection,
      });

      if (permissionGranted) {
        this.notificationsSent.push({
          title: '🔴 🍃 VertiFarm Alert',
          body: alert.description,
          data: { alertId: alert.id, metric: alert.metric },
        });
      }

      return alert;
    }

    // Recovery
    if (existing && !evaluation.isViolation) {
      existing.alert.isResolved = true;
      this.activeAlerts.delete(key);
      return null;
    }

    return null;
  }
}

async function runTests() {
  console.log('\n=== RUNNING VERTIFARM ALERT TESTS (NODE.JS) ===\n');

  // Test 1: Normal readings
  console.log('[Test 1] Readings within normal ranges');
  {
    const cases = [
      ['temperature', 25.0],
      ['humidity', 70.0],
      ['soilMoisture', 50.0],
      ['ph', 6.5],
      ['tds', 650.0],
      ['light', 1500.0],
    ];
    for (const [m, v] of cases) {
      const res = evaluateSensorThreshold(m, v);
      assert(res.isValid && !res.isViolation && res.status === 'healthy', `${m} at ${v} is healthy`);
    }
  }

  // Test 2: Specific violations
  console.log('\n[Test 2] High temperature, low humidity, low soil moisture, high light');
  {
    const tempRes = evaluateSensorThreshold('temperature', 34.0);
    assert(tempRes.isViolation, '34°C triggers violation');
    assert(tempRes.severity === 'warning', '34°C is warning severity');
    assert(tempRes.notificationBody.includes('High temperature detected: 34.0 °C — Normal range: 20.0–30.0 °C'), 'Temp body formatted correctly');

    const humRes = evaluateSensorThreshold('humidity', 35.0);
    assert(humRes.isViolation && humRes.severity === 'critical', '35% humidity is critical');
    assert(humRes.notificationBody.includes('Humidity critical: 35.0 % — Minimum: 60.0 %'), 'Hum body formatted correctly');

    const soilRes = evaluateSensorThreshold('soilMoisture', 25.0);
    assert(soilRes.isViolation && soilRes.severity === 'critical', '25% soil moisture is critical');
    assert(soilRes.notificationBody.includes('Soil Moisture critical: 25.0 % — Minimum: 40.0 %'), 'Soil moisture body formatted correctly');

    const lightRes = evaluateSensorThreshold('light', 3500.0);
    assert(lightRes.isViolation && lightRes.severity === 'critical', '3500 Lux is critical');
    assert(lightRes.notificationBody.includes('Light Intensity critical: 3,500 Lux — Maximum: 2,000 Lux'), 'Light body formatted correctly');
  }

  // Test 3: Min and Max boundaries
  console.log('\n[Test 3] Boundary validation across all 6 metrics');
  {
    for (const [metric, cfg] of Object.entries(SENSOR_THRESHOLDS)) {
      const low = evaluateSensorThreshold(metric, cfg.optimalMin - 0.5);
      assert(low.isViolation && low.violationDirection === 'low', `${metric} below optimalMin triggers low alert`);

      const high = evaluateSensorThreshold(metric, cfg.optimalMax + 0.5);
      assert(high.isViolation && high.violationDirection === 'high', `${metric} above optimalMax triggers high alert`);
    }
  }

  // Test 4: Invalid and missing readings
  console.log('\n[Test 4] Invalid and missing readings');
  {
    const invalids = [null, undefined, '', NaN, Infinity, -100, 200000];
    for (const v of invalids) {
      const res = evaluateSensorThreshold('temperature', v);
      assert(!res.isValid && !res.isViolation, `Invalid reading ${v} is rejected without alert`);
    }
  }

  // Test 5: Duplicate alert suppression
  console.log('\n[Test 5] Duplicate alert suppression');
  {
    const monitor = new MockSensorAlertMonitor();
    const r1 = { farmId: 'farm-1', metric: 'temperature', value: 34.0 };

    const a1 = await monitor.processReading(r1);
    assert(a1 !== null, 'Initial violation creates alert');
    assert(monitor.notificationsSent.length === 1, 'Initial violation sends 1 notification');

    // Repeated reading
    const a2 = await monitor.processReading({ ...r1, value: 34.5 });
    assert(a2 === null, 'Repeated violation is suppressed');
    assert(monitor.notificationsSent.length === 1, 'No duplicate notification sent');

    // 3rd reading
    const a3 = await monitor.processReading({ ...r1, value: 33.8 });
    assert(a3 === null, '3rd reading is suppressed');
    assert(monitor.notificationsSent.length === 1, 'Still only 1 notification sent');
  }

  // Test 6: Recovery and re-alerting
  console.log('\n[Test 6] Recovery and re-alerting with hysteresis');
  {
    const monitor = new MockSensorAlertMonitor();
    // 1. Violation
    await monitor.processReading({ farmId: 'farm-1', metric: 'temperature', value: 34.0 });
    assert(monitor.activeAlerts.size === 1, 'Active alert exists');

    // 2. Flutter at 29.8°C (hysteresis is 0.5, optimalMax 30 -> limit 29.5)
    await monitor.processReading({ farmId: 'farm-1', metric: 'temperature', value: 29.8 });
    assert(monitor.activeAlerts.size === 1, 'Hysteresis prevents premature resolution at 29.8°C');

    // 3. True recovery (24°C)
    await monitor.processReading({ farmId: 'farm-1', metric: 'temperature', value: 24.0 });
    assert(monitor.activeAlerts.size === 0, 'Alert resolved when reading reaches 24°C');

    // 4. Re-alerting allowed
    const aNew = await monitor.processReading({ farmId: 'farm-1', metric: 'temperature', value: 35.0 });
    assert(aNew !== null, 'New alert triggered upon second violation');
    assert(monitor.notificationsSent.length === 2, '2nd notification dispatched after recovery');
  }

  // Test 7: Multi-sensor simultaneous violations
  console.log('\n[Test 7] Multi-sensor simultaneous violations');
  {
    const monitor = new MockSensorAlertMonitor();
    await monitor.processReading({ farmId: 'farm-1', metric: 'temperature', value: 34.0 });
    await monitor.processReading({ farmId: 'farm-1', metric: 'humidity', value: 32.0 });
    await monitor.processReading({ farmId: 'farm-1', metric: 'soilMoisture', value: 20.0 });

    assert(monitor.activeAlerts.size === 3, '3 independent sensor alerts tracked');
    assert(monitor.notificationsSent.length === 3, '3 distinct notifications dispatched');
  }

  // Test 8: Permission denial
  console.log('\n[Test 8] Notification permission denial handling');
  {
    const monitor = new MockSensorAlertMonitor();
    const alert = await monitor.processReading(
      { farmId: 'farm-1', metric: 'temperature', value: 34.0 },
      false // permission denied
    );
    assert(alert !== null, 'Alert created in memory');
    assert(monitor.notificationsSent.length === 0, 'Notification skipped when permissions denied');
  }

  // Test 9: Notification tap navigation simulation
  console.log('\n[Test 9] Notification tap navigation simulation');
  {
    let routedScreen = null;
    const handleTap = (data) => {
      if (data && data.alertId) {
        routedScreen = `/alerts/${data.alertId}`;
      } else if (data && data.metric) {
        routedScreen = `/live-data/${data.metric}`;
      } else {
        routedScreen = '/alerts';
      }
    };

    handleTap({ alertId: 'alert-temp-999', metric: 'temperature' });
    assert(routedScreen === '/alerts/alert-temp-999', 'Tap navigates to /alerts/alert-temp-999');

    handleTap({ metric: 'humidity' });
    assert(routedScreen === '/live-data/humidity', 'Tap with metric only navigates to /live-data/humidity');
  }

  console.log('\n=== SUMMARY ===');
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);

  if (failed > 0) {
    process.exit(1);
  } else {
    console.log('\n🎉 ALL SENSOR ALERT VERIFICATION TESTS PASSED SUCCESSFULLY!\n');
  }
}

runTests();
