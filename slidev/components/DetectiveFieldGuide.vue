<script setup lang="ts">
const props = withDefaults(defineProps<{
  active?: number
  compact?: boolean
}>(), {
  active: 0,
  compact: false,
})

const steps = [
  { verb: 'Find', detail: 'the right run' },
  { verb: 'Choose', detail: 'live or history' },
  { verb: 'Localize', detail: 'the costly stage' },
  { verb: 'Inspect', detail: 'the task shape' },
  { verb: 'Correlate', detail: 'plan · executors · logs' },
  { verb: 'Test', detail: 'one hypothesis' },
]

function state(index: number) {
  if (!props.active) return 'idle'
  if (index + 1 === props.active) return 'active'
  if (index + 1 < props.active) return 'done'
  return 'muted'
}
</script>

<template>
  <div class="field-guide" :class="{ compact }" aria-label="Spark Detective field guide">
    <div
      v-for="(step, index) in steps"
      :key="step.verb"
      class="guide-step"
      :class="state(index)"
    >
      <div class="step-number">{{ index + 1 }}</div>
      <div class="step-verb">{{ step.verb }}</div>
      <div class="step-detail">{{ step.detail }}</div>
    </div>
  </div>
</template>

<style scoped>
.field-guide {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1.15rem;
  margin: 2.25rem 0 1.25rem;
}

.guide-step {
  position: relative;
  min-height: 9.5rem;
  padding: 1.05rem 0.7rem 0.8rem;
  border: 2px solid #cbd5e1;
  border-radius: 1rem;
  background: #f8fafc;
  text-align: center;
  transition: opacity 180ms ease, transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.guide-step:not(:last-child)::after {
  content: '›';
  position: absolute;
  z-index: 2;
  top: 3.25rem;
  right: -1rem;
  width: 0.8rem;
  color: #94a3b8;
  font-size: 2rem;
  font-weight: 800;
}

.step-number {
  display: grid;
  width: 2.1rem;
  height: 2.1rem;
  margin: 0 auto 0.65rem;
  place-items: center;
  border-radius: 999px;
  background: #e2e8f0;
  color: #334155;
  font-weight: 800;
}

.step-verb {
  color: #0f172a;
  font-size: 1.25rem;
  font-weight: 800;
}

.step-detail {
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.82rem;
  line-height: 1.25;
}

.guide-step.active {
  transform: translateY(-0.4rem) scale(1.04);
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 0.8rem 1.6rem rgb(37 99 235 / 16%);
}

.guide-step.active .step-number {
  background: #2563eb;
  color: white;
}

.guide-step.done {
  border-color: #86efac;
  background: #f0fdf4;
}

.guide-step.done .step-number {
  background: #16a34a;
  color: white;
}

.guide-step.muted {
  opacity: 0.42;
}

.field-guide.compact {
  gap: 0.8rem;
  margin: 0.75rem 0 1.35rem;
}

.compact .guide-step {
  min-height: 5.6rem;
  padding: 0.65rem 0.4rem 0.45rem;
  border-radius: 0.75rem;
}

.compact .guide-step:not(:last-child)::after {
  top: 1.7rem;
  right: -0.75rem;
  font-size: 1.5rem;
}

.compact .step-number {
  width: 1.55rem;
  height: 1.55rem;
  margin-bottom: 0.3rem;
  font-size: 0.75rem;
}

.compact .step-verb {
  font-size: 0.92rem;
}

.compact .step-detail {
  margin-top: 0.12rem;
  font-size: 0.62rem;
}
</style>
