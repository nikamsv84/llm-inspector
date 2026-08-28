<script setup>
import { computed } from 'vue'

const props = defineProps({
  packet: {
    type: Object,
    default: null
  }
})

// شی security_details که از بک‌اند میاد:
// { risk_score: float, matched_patterns: [], flags: { combined_model_override, body_malicious_probablity, header_malicious_probablity, "Xss/Sqli detection: " } }
const securityDetails = computed(() => props.packet?.security_details || null)

const riskScore = computed(() => {
  const s = securityDetails.value?.risk_score
  return typeof s === 'number' ? s : 0
})

const riskPercent = computed(() => Math.round(Math.min(Math.max(riskScore.value, 0), 1) * 100))

const riskLevel = computed(() => {
  const p = riskPercent.value
  if (p >= 70) return 'critical'
  if (p >= 40) return 'warning'
  if (p > 0) return 'low'
  return 'clean'
})

const riskLabel = computed(() => {
  const map = { critical: 'critical', warning: 'warning', low: 'low', clean: 'clean' }
  return map[riskLevel.value]
})

const flags = computed(() => securityDetails.value?.flags || {})

const headerProb = computed(() => {
  const v = flags.value.header_malicious_probablity
  return typeof v === 'number' ? Math.round(v * 100) : 0
})

const bodyProb = computed(() => {
  const v = flags.value.body_malicious_probablity
  return typeof v === 'number' ? Math.round(v * 100) : 0
})

const xssSqliDetected = computed(() => {
  // اسم کلید توی analyzer به صورت "Xss/Sqli detection: " با فاصله انتهایی ذخیره شده
  const raw =
    flags.value['Xss/Sqli detection: '] ??
    flags.value['xss_sqli_detected'] ??
    ''
  return raw && String(raw).length > 0 ? String(raw) : null
})

const combinedOverride = computed(() => !!flags.value.combined_model_override)

const matchedPatterns = computed(() => {
  const p = securityDetails.value?.matched_patterns
  return Array.isArray(p) ? p : []
})

const hasSecurityData = computed(() => !!securityDetails.value)
</script>

<template>
  <div class="console-container">
    <div class="console-title">🛡️ Security Console</div>

    <!-- حالتی که هیچ پکتی انتخاب نشده -->
    <div v-if="!packet" class="console-placeholder">
      select a packet for visiting security details.
    </div>

    <!-- حالتی که پکت انتخاب شده ولی داده امنیتی نداره -->
    <div v-else-if="!hasSecurityData" class="console-placeholder">
      no security info
    </div>

    <!-- نمایش اصلی -->
    <div v-else class="console-content">

      <!-- ردیف بالا: امتیاز ریسک + وضعیت کلی -->
      <div class="risk-summary" :class="'risk-' + riskLevel">
        <div class="risk-score-ring">
          <svg viewBox="0 0 100 100" class="ring-svg">
            <circle cx="50" cy="50" r="42" class="ring-bg" />
            <circle
              cx="50" cy="50" r="42"
              class="ring-fg"
              :stroke-dasharray="264"
              :stroke-dashoffset="264 - (264 * riskPercent) / 100"
            />
          </svg>
          <div class="ring-label">
            <span class="ring-percent">{{ riskPercent }}%</span>
            <span class="ring-sub">ریسک</span>
          </div>
        </div>

        <div class="risk-info">
          <div class="risk-badge" :class="'badge-' + riskLevel">
            {{ riskLabel }}
          </div>
          <div class="risk-meta">
            <span v-if="combinedOverride" class="chip chip-override">
              ⚡ Model Override
            </span>
            <span v-if="xssSqliDetected" class="chip chip-danger">
              🚨 {{ xssSqliDetected }}
            </span>
            <span v-if="!combinedOverride && !xssSqliDetected" class="chip chip-neutral">
              no critical pattern
            </span>
          </div>
        </div>
      </div>

      <!-- ردیف میانی: احتمال بدخواهانه بودن هدر/بادی -->
      <div class="prob-grid">
        <div class="prob-item">
          <div class="prob-header">
            <span class="prob-label">Header Maliciousness</span>
            <span class="prob-value">{{ headerProb }}%</span>
          </div>
          <div class="prob-bar-track">
            <div
              class="prob-bar-fill"
              :class="headerProb >= 70 ? 'fill-critical' : headerProb >= 40 ? 'fill-warning' : 'fill-low'"
              :style="{ width: headerProb + '%' }"
            ></div>
          </div>
        </div>

        <div class="prob-item">
          <div class="prob-header">
            <span class="prob-label">Body Maliciousness</span>
            <span class="prob-value">{{ bodyProb }}%</span>
          </div>
          <div class="prob-bar-track">
            <div
              class="prob-bar-fill"
              :class="bodyProb >= 70 ? 'fill-critical' : bodyProb >= 40 ? 'fill-warning' : 'fill-low'"
              :style="{ width: bodyProb + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- ردیف پایین: matched patterns -->
      <div class="patterns-block">
        <div class="patterns-title">Matched Patterns</div>
        <div v-if="matchedPatterns.length === 0" class="no-patterns">
          no pattern matching
        </div>
        <div v-else class="patterns-list">
          <span
            v-for="(pattern, idx) in matchedPatterns"
            :key="idx"
            class="pattern-tag"
          >
            {{ pattern }}
          </span>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.console-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.console-title {
  font-size: 0.85rem;
  color: #c084fc;
  font-weight: 600;
  margin-bottom: 8px;
}

.console-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 0.8rem;
  border: 1px dashed #2e2348;
  border-radius: 8px;
  text-align: center;
  padding: 12px;
}

.console-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* --- Risk Summary --- */
.risk-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #110d21;
  border: 1px solid #1e1738;
  border-radius: 10px;
  padding: 12px 16px;
}

.risk-score-ring {
  position: relative;
  width: 76px;
  height: 76px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: #1e1738;
  stroke-width: 8;
}

.ring-fg {
  fill: none;
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.4s ease, stroke 0.4s ease;
}

.risk-clean .ring-fg,
.risk-low .ring-fg { stroke: #34d399; }
.risk-warning .ring-fg { stroke: #facc15; }
.risk-critical .ring-fg { stroke: #f87171; }

.ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring-percent {
  font-size: 1rem;
  font-weight: 700;
  color: #e2e8f0;
}

.ring-sub {
  font-size: 0.6rem;
  color: #64748b;
}

.risk-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.risk-badge {
  display: inline-block;
  width: fit-content;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.badge-clean, .badge-low {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border: 1px solid #059669;
}

.badge-warning {
  background: rgba(250, 204, 21, 0.15);
  color: #facc15;
  border: 1px solid #ca8a04;
}

.badge-critical {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
  border: 1px solid #dc2626;
  animation: pulse-danger 1.6s ease-in-out infinite;
}

@keyframes pulse-danger {
  0%, 100% { box-shadow: 0 0 0 rgba(248, 113, 113, 0); }
  50% { box-shadow: 0 0 10px rgba(248, 113, 113, 0.5); }
}

.risk-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  font-size: 0.7rem;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap;
}

.chip-override {
  background: rgba(217, 70, 239, 0.15);
  color: #e879f9;
  border: 1px solid #a21caf;
}

.chip-danger {
  background: rgba(248, 113, 113, 0.15);
  color: #f87171;
  border: 1px solid #dc2626;
}

.chip-neutral {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
  border: 1px solid #334155;
}

/* --- Probability bars --- */
.prob-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.prob-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #110d21;
  border: 1px solid #1e1738;
  border-radius: 8px;
  padding: 10px 12px;
}

.prob-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prob-label {
  font-size: 0.7rem;
  color: #94a3b8;
  text-transform: uppercase;
}

.prob-value {
  font-size: 0.8rem;
  font-weight: 700;
  color: #e2e8f0;
}

.prob-bar-track {
  height: 6px;
  border-radius: 999px;
  background: #1e1738;
  overflow: hidden;
}

.prob-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.fill-low { background: #34d399; }
.fill-warning { background: #facc15; }
.fill-critical { background: #f87171; }

/* --- Matched patterns --- */
.patterns-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.patterns-title {
  font-size: 0.7rem;
  color: #a855f7;
  font-weight: 700;
  text-transform: uppercase;
}

.no-patterns {
  color: #64748b;
  font-size: 0.75rem;
  padding: 8px 0;
}

.patterns-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pattern-tag {
  font-family: 'Fira Code', monospace;
  font-size: 0.7rem;
  background: #1a1430;
  color: #d8b4fe;
  border: 1px solid #4c3a75;
  padding: 3px 8px;
  border-radius: 6px;
}
</style>