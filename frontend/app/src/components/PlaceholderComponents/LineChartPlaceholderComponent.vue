<template>
  <div class="line-chart-placeholder placeholder-glow" aria-hidden="true">
    <svg
      class="w-100 h-100"
      viewBox="0 0 200 100"
      preserveAspectRatio="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- Fill area below the line -->
      <path
        class="chart-fill placeholder"
        d="M0,65 C15,60 20,42 35,38 C50,34 55,52 70,48 C85,44 90,18 105,14 C120,10 125,32 140,28 C155,24 160,46 175,42 C190,38 196,54 200,50 L200,100 L0,100 Z"
      />
      <!-- Line itself -->
      <path
        class="chart-line placeholder"
        d="M0,65 C15,60 20,42 35,38 C50,34 55,52 70,48 C85,44 90,18 105,14 C120,10 125,32 140,28 C155,24 160,46 175,42 C190,38 196,54 200,50"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
// No props needed — the SVG path is purely decorative.
</script>

<style scoped>
.line-chart-placeholder {
  max-height: 300px;
  height: 200px;
  width: 100%;
}

.chart-fill {
  fill: var(--bs-secondary);
  opacity: 0.35;
}

.chart-line {
  fill: none;
  stroke: var(--bs-secondary);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
