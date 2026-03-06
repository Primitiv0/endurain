<template>
  <LoadingComponent v-if="isLoading" />
  <canvas ref="chartCanvas" class="chart-canvas" v-else></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import LoadingComponent from '@/components/GeneralComponents/LoadingComponent.vue'

import { Chart, registerables } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
Chart.register(...registerables, zoomPlugin)

const props = defineProps({
  userHealthTargets: {
    type: [Object, null],
    required: true
  },
  userHealthPoop: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    required: true
  }
})

const { t } = useI18n()
const chartCanvas = ref(null)
let myChart = null

const crosshairPlugin = {
  id: 'customCrosshair',
  afterDraw: (chart) => {
    if (chart.tooltip?._active && chart.tooltip._active.length) {
      const ctx = chart.ctx
      const activePoint = chart.tooltip._active[0]
      const x = activePoint.element.x
      const topY = chart.scales.y.top
      const bottomY = chart.scales.y.bottom

      ctx.save()
      ctx.beginPath()
      ctx.setLineDash([5, 5])
      ctx.moveTo(x, topY)
      ctx.lineTo(x, bottomY)
      ctx.lineWidth = 1
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)'
      ctx.stroke()
      ctx.restore()
    }
  }
}

/** Aggregate poop records into count-per-day for bar chart. */
const chartData = computed(() => {
  if (!props.userHealthPoop || props.userHealthPoop.length === 0) {
    return { datasets: [], labels: [] }
  }

  const countByDate = {}
  for (const record of props.userHealthPoop) {
    const dateKey = record.date_time.slice(0, 10)
    countByDate[dateKey] = (countByDate[dateKey] || 0) + 1
  }

  const sortedDates = Object.keys(countByDate).sort()
  const data = sortedDates.map((d) => countByDate[d])
  const labels = sortedDates.map((d) => {
    const parts = d.split('-')
    return `${parseInt(parts[2])}/${parseInt(parts[1])}/${parts[0]}`
  })

  const datasets = [
    {
      label: t('healthPoopZoneComponent.labelPoopCount'),
      data,
      backgroundColor: 'rgba(59, 130, 246, 0.4)',
      borderColor: 'rgba(59, 130, 246, 0.8)',
      borderWidth: 0,
      borderRadius: 4
    }
  ]

  if (props.userHealthTargets?.poop_count != null) {
    datasets.push({
      label: t('healthPoopZoneComponent.labelPoopTarget'),
      data: Array(labels.length).fill(Number(props.userHealthTargets.poop_count)),
      type: 'line',
      borderColor: 'rgba(107, 114, 128, 0.9)',
      borderWidth: 2,
      borderDash: [5, 5],
      fill: false,
      pointRadius: 0,
      pointHoverRadius: 0
    })
  }

  return { datasets, labels }
})

function createChart() {
  if (!chartCanvas.value) return
  if (myChart) {
    myChart.destroy()
    myChart = null
  }

  myChart = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'bar',
    data: chartData.value,
    plugins: [crosshairPlugin],
    options: {
      responsive: true,
      animation: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 },
          grid: { lineWidth: 1, drawBorder: true, borderWidth: 1 }
        },
        x: {
          autoSkip: true,
          ticks: { maxTicksLimit: 10, autoSkip: true },
          grid: { lineWidth: 1, drawBorder: true, borderWidth: 1 }
        }
      },
      plugins: {
        tooltip: {
          enabled: true,
          callbacks: {
            label: function (context) {
              const label = context.dataset.label || ''
              const value = context.parsed.y
              if (value === null || value === undefined) return `${label}: N/A`
              return `${label}: ${value}`
            }
          }
        },
        zoom: {
          pan: { enabled: true, mode: 'x', modifierKey: 'shift' },
          zoom: {
            wheel: { enabled: true, speed: 0.1 },
            pinch: { enabled: true },
            mode: 'x'
          },
          limits: { x: { min: 'original', max: 'original' } }
        }
      }
    }
  })
}

watch(
  chartData,
  (newChartData) => {
    if (myChart) {
      myChart.data = newChartData
      myChart.update()
    }
  },
  { deep: true }
)

watch(
  () => props.isLoading,
  (newVal, oldVal) => {
    if (oldVal === true && newVal === false) {
      nextTick(() => {
        createChart()
      })
    }
  }
)

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  if (myChart) {
    myChart.destroy()
    myChart = null
  }
})
</script>

<style scoped>
.chart-canvas {
  max-height: 300px;
  width: 100%;
}
</style>
