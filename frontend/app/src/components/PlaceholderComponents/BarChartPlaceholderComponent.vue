<template>
  <div class="chart-placeholder d-flex align-items-end justify-content-evenly" aria-hidden="true">
    <div
      v-for="n in numberOfBars"
      :key="n"
      class="placeholder-glow flex-fill mx-1 h-100 d-flex align-items-end"
    >
      <span
        class="placeholder bg-secondary rounded d-block w-100"
        :style="{ height: barHeights[(n - 1) % barHeights.length] + '%' }"
      ></span>
    </div>
  </div>
</template>

<script setup lang="ts">
/** Pre-computed pseudo-random bar heights to simulate a chart skeleton. */
const BAR_HEIGHTS = [45, 70, 55, 85, 40, 65, 90, 50, 75, 60]

defineProps<{
  /** Number of placeholder bars to display. */
  numberOfBars?: number
}>()

/** Returns a fixed set of varied bar heights for visual realism. */
const barHeights = BAR_HEIGHTS
</script>

<style scoped>
.chart-placeholder {
  max-height: 300px;
  height: 200px;
  width: 100%;
}
</style>
