<template>
  <LoadingComponent v-if="isLoading" />
  <canvas ref="chartCanvas" class="chart-canvas" v-else></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import LoadingComponent from '@/components/GeneralComponents/LoadingComponent.vue'
import { useAuthStore } from '@/stores/authStore'
import { mlToFlOz } from '@/utils/unitsUtils'

import { Chart, registerables } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
Chart.register(...registerables, zoomPlugin)

const props = defineProps({
  userHealthTargets: {
    type: [Object, null],
    required: true
  },
  userHealthWater: {
    type: Array,
    required: true
  },
  isLoading: {
    type: Boolean,
    required: true
  }
})

const { t } = useI18n()
const authStore = useAuthStore()
const isImperial = authStore?.user?.units === 'imperial'
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

const chartData = computed(() => {
  if (!props.userHealthWater || props.userHealthWater.length === 0) {
    return { datasets: [], labels: [] }
  }

  const sorted = [...props.userHealthWater].sort((a, b) => new Date(a.date) - new Date(b.date))

  const data = []
  const labels = []

  for (const record of sorted) {
    data.push(isImperial ? mlToFlOz(Number(record.amount_ml)) : Number(record.amount_ml))
    const d = new Date(record.date)
    labels.push(`${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`)
  }

  const unit = isImperial ? t('generalItems.unitsFlOz') : t('generalItems.unitsMl')

  const datasets = [
    {
      label: t('healthWaterZoneComponent.labelWaterMl'),
      data,
      backgroundColor: 'rgba(59, 130, 246, 0.4)',
      borderColor: 'rgba(59, 130, 246, 0.8)',
      borderWidth: 0,
      borderRadius: 4
    }
  ]

  if (props.userHealthTargets?.water_ml != null) {
    const targetValue = isImperial
      ? mlToFlOz(Number(props.userHealthTargets.water_ml))
      : Number(props.userHealthTargets.water_ml)
    datasets.push({
      label: t('healthWaterZoneComponent.labelWaterTarget'),
      data: Array(labels.length).fill(targetValue),
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
              return `${label}: ${value} ${isImperial ? t('generalItems.unitsFlOz') : t('generalItems.unitsMl')}`
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
  () => props.isLoading,
  (newVal, oldVal) => {
    if (oldVal === true && newVal === false) {
      nextTick(() => {
        createChart()
      })
    }
  }
)

watch(
  () => props.userHealthWater,
  () => {
    if (!props.isLoading) {
      nextTick(() => {
        createChart()
      })
    }
  },
  { deep: true }
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
