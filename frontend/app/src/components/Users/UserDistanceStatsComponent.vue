<template>
  <!-- Metric toggle -->
  <div class="btn-group d-flex mb-3" role="group">
    <input
      type="radio"
      class="btn-check"
      name="statsMetricToggle"
      id="btnMetricDistance"
      autocomplete="off"
      value="distance"
      v-model="selectedMetric"
    />
    <label class="btn btn-outline-primary" for="btnMetricDistance">
      {{ $t('userDistanceStats.toggleDistance') }}
    </label>
    <input
      type="radio"
      class="btn-check"
      name="statsMetricToggle"
      id="btnMetricTime"
      autocomplete="off"
      value="time"
      v-model="selectedMetric"
    />
    <label class="btn btn-outline-primary" for="btnMetricTime">
      {{ $t('userDistanceStats.toggleTime') }}
    </label>
    <input
      type="radio"
      class="btn-check"
      name="statsMetricToggle"
      id="btnMetricCalories"
      autocomplete="off"
      value="calories"
      v-model="selectedMetric"
    />
    <label class="btn btn-outline-primary" for="btnMetricCalories">
      {{ $t('userDistanceStats.toggleCalories') }}
    </label>
  </div>

  <div class="text-center">
    <span>{{ $t('userDistanceStats.thisWeekDistancesTitle') }}</span>
  </div>
  <div class="row mt-3 text-center">
    <div class="col" v-for="sport in thisWeek" :key="sport.key">
      <font-awesome-icon :icon="['fas', sport.icon]" size="2x" />
      <br />
      {{ formatValue(sport) }}
      <span v-if="selectedMetric === 'distance'">
        <span v-if="authStore?.user?.units === 'metric'">
          <span v-if="sport.useMeters">{{ $t('generalItems.unitsM') }}</span>
          <span v-else>{{ $t('generalItems.unitsKm') }}</span>
        </span>
        <span v-else>
          <span v-if="sport.useMeters">{{ $t('generalItems.unitsYards') }}</span>
          <span v-else>{{ $t('generalItems.unitsMiles') }}</span>
        </span>
      </span>
      <span v-else-if="selectedMetric === 'calories'">
        {{ $t('generalItems.unitsCalories') }}
      </span>
    </div>
  </div>

  <hr />

  <div class="text-center">
    <span>{{ $t('userDistanceStats.thisMonthDistancesTitle') }}</span>
  </div>
  <div class="row mt-3 text-center">
    <div class="col" v-for="sport in thisMonth" :key="sport.key">
      <font-awesome-icon :icon="['fas', sport.icon]" size="2x" />
      <br />
      {{ formatValue(sport) }}
      <span v-if="selectedMetric === 'distance'">
        <span v-if="authStore?.user?.units === 'metric'">
          <span v-if="sport.useMeters">{{ $t('generalItems.unitsM') }}</span>
          <span v-else>{{ $t('generalItems.unitsKm') }}</span>
        </span>
        <span v-else>
          <span v-if="sport.useMeters">{{ $t('generalItems.unitsYards') }}</span>
          <span v-else>{{ $t('generalItems.unitsMiles') }}</span>
        </span>
      </span>
      <span v-else-if="selectedMetric === 'calories'">
        {{ $t('generalItems.unitsCalories') }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { metersToKm, metersToMiles, metersToYards } from '@/utils/unitsUtils'

const props = defineProps({
  thisWeekStats: {
    type: Object,
    required: true
  },
  thisMonthStats: {
    type: Object,
    required: true
  }
})

const authStore = useAuthStore()
const selectedMetric = ref('distance')

// Sport definitions: backend key → display icon and unit behaviour.
// useMeters: true → display in metres (metric) or yards (imperial) instead of km/miles.
const SPORT_DEFINITIONS = [
  { key: 'run', icon: 'person-running', useMeters: false },
  { key: 'bike', icon: 'person-biking', useMeters: false },
  { key: 'swim', icon: 'person-swimming', useMeters: true },
  { key: 'walk', icon: 'person-walking', useMeters: false },
  { key: 'hike', icon: 'person-hiking', useMeters: false },
  { key: 'rowing', icon: 'sailboat', useMeters: false },
  { key: 'snow_ski', icon: 'person-skiing', useMeters: false },
  { key: 'snowboard', icon: 'person-snowboarding', useMeters: false },
  { key: 'windsurf', icon: 'wind', useMeters: false },
  { key: 'stand_up_paddleboarding', icon: 'water', useMeters: false },
  { key: 'surfing', icon: 'water', useMeters: false },
  { key: 'kayaking', icon: 'water', useMeters: false },
  { key: 'sailing', icon: 'sailboat', useMeters: false },
  { key: 'snowshoeing', icon: 'person-hiking', useMeters: false },
  { key: 'inline_skating', icon: 'person-skating', useMeters: false }
]

/**
 * Format a total-seconds value as H:MM.
 */
function formatTime(seconds) {
  if (!seconds) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}:${String(m).padStart(2, '0')}`
}

const getTopThree = (stats) => {
  const isMetric = authStore?.user?.units === 'metric'

  return SPORT_DEFINITIONS.map((sport) => {
    const sportStats = stats?.[sport.key] ?? { distance: 0, time: 0, calories: 0 }

    // Convert raw metres into the display unit for the distance metric.
    const displayDistance = sport.useMeters
      ? isMetric
        ? sportStats.distance
        : metersToYards(sportStats.distance)
      : isMetric
        ? metersToKm(sportStats.distance)
        : metersToMiles(sportStats.distance)

    // The sort value changes with the selected metric.
    const sortValue =
      selectedMetric.value === 'distance'
        ? sportStats.distance
        : selectedMetric.value === 'time'
          ? sportStats.time
          : sportStats.calories

    return {
      ...sport,
      displayDistance,
      rawTime: sportStats.time,
      rawCalories: sportStats.calories,
      sortValue
    }
  })
    .sort((a, b) => b.sortValue - a.sortValue)
    .slice(0, 3)
}

/**
 * Return the formatted display string for the currently selected metric.
 */
function formatValue(sport) {
  if (selectedMetric.value === 'distance') {
    return Math.floor(sport.displayDistance) + ' '
  }
  if (selectedMetric.value === 'time') {
    return formatTime(sport.rawTime) + ' '
  }
  return Math.floor(sport.rawCalories || 0) + ' '
}

const thisWeek = computed(() => getTopThree(props.thisWeekStats))
const thisMonth = computed(() => getTopThree(props.thisMonthStats))
</script>
