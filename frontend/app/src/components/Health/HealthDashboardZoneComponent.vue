<template>
  <div class="col">
    <div class="row">
      <!-- Today's sleep -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.sleep')"
        :is-loading="isLoadingParent || isLoading"
        :value="sleepDisplay"
        :no-data-label="$t('generalItems.labelNoData')"
        :target-display-value="sleepTargetDisplay"
        :no-target-label="$t('healthDashboardZoneComponent.noSleepTarget')"
        :arrow-direction="sleepArrowDirection"
      />

      <!-- Resting heart rate -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.restingHeartRate')"
        :is-loading="isLoadingParent || isLoading"
        :value="restingHrDisplay"
        :no-data-label="$t('generalItems.labelNoData')"
        :footer-text="hrvFooterText"
      />

      <!-- Avg skin temperature deviation -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.avgSkinTemperatureDeviation')"
        :is-loading="isLoadingParent || isLoading"
        :value="skinTempDisplay"
        :no-data-label="$t('generalItems.labelNoData')"
        :footer-text="$t('generalItems.labelNoData')"
      />

      <!-- Weight -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.weight')"
        :is-loading="isLoadingParent || isLoading"
        :value="weightDisplay"
        :no-data-label="$t('generalItems.labelNotApplicable')"
        :target-display-value="weightTargetDisplay"
        :no-target-label="$t('healthDashboardZoneComponent.noWeightTarget')"
        :arrow-direction="weightArrowDirection"
      />

      <!-- BMI -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.bmi')"
        :is-loading="isLoadingParent || isLoading"
        :value="bmiDisplay"
        :no-data-label="$t('generalItems.labelNotApplicable')"
        :footer-text="bmiFooterText"
      />

      <!-- Today's steps -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.steps')"
        :is-loading="isLoadingParent || isLoading"
        :value="stepsDisplay"
        :no-data-label="$t('generalItems.labelNotApplicable')"
        :target-display-value="stepsTargetDisplay"
        :no-target-label="$t('healthDashboardZoneComponent.noStepsTarget')"
        :arrow-direction="stepsArrowDirection"
      />

      <!-- Fasting -->
      <HealthDashboardCardComponent
        :title="$t('healthDashboardZoneComponent.fasting')"
        :is-loading="isLoadingParent || isLoading"
        :value="fastingDisplay"
        :no-data-label="$t('generalItems.labelNoData')"
        :subtitle="fastingSubtitle"
        :target-display-value="fastingTargetDisplay"
        :no-target-label="$t('healthDashboardZoneComponent.noFastingTarget')"
        :arrow-direction="fastingArrowDirection"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
// Importing the stores
import { useAuthStore } from '@/stores/authStore'
import { kgToLbs } from '@/utils/unitsUtils'
import { formatSecondsToHoursMinutes } from '@/utils/dateTimeUtils'
import { getHrvStatusI18nKey } from '@/utils/healthUtils'
// Import services
import { health } from '@/services/healthService'
// Import components
import HealthDashboardCardComponent from './HealthDashboardZone/HealthDashboardCardComponent.vue'

const props = defineProps({
  userHealthTargets: {
    type: [Object, null],
    required: true
  },
  isLoadingParent: {
    type: Boolean,
    required: true
  }
})

const { t } = useI18n()
const isLoading = ref(false)
const healthDashboardData = ref(null)
const authStore = useAuthStore()
const currentWeight = ref(null)
const currentBMI = ref(null)
const bmiDescription = ref(null)
const todaySteps = ref(null)
const todaySleep = ref(null)
const restingHeartRate = ref(null)
const hrvStatus = ref(null)
const avgSkinTempDeviation = ref(null)
const activeFasting = ref(null)
const activeFastingElapsed = ref(0)

// Sleep computed properties
const sleepDisplay = computed(() =>
  todaySleep.value ? formatSecondsToHoursMinutes(todaySleep.value) : null
)
const sleepTargetDisplay = computed(() =>
  props.userHealthTargets?.sleep ? formatSecondsToHoursMinutes(props.userHealthTargets.sleep) : null
)
const sleepArrowDirection = computed(() => {
  if (!props.userHealthTargets?.sleep) return null
  return todaySleep.value < props.userHealthTargets.sleep ? 'down' : 'up'
})

// Resting heart rate computed properties
const restingHrDisplay = computed(() =>
  restingHeartRate.value ? `${restingHeartRate.value} ${t('generalItems.unitsBpm')}` : null
)
const hrvFooterText = computed(() =>
  hrvStatus.value ? t(getHrvStatusI18nKey(hrvStatus.value)) : t('generalItems.labelNoData')
)

// Skin temperature computed property
const skinTempDisplay = computed(() =>
  avgSkinTempDeviation.value
    ? `${avgSkinTempDeviation.value} ${t('generalItems.unitsCelsius')}`
    : null
)

// Weight computed properties
const weightDisplay = computed(() => {
  if (!currentWeight.value) return null
  if (authStore?.user?.units === 'metric')
    return `${currentWeight.value} ${t('generalItems.unitsKg')}`
  return `${kgToLbs(currentWeight.value)} ${t('generalItems.unitsLbs')}`
})
const weightTargetDisplay = computed(() => {
  if (!props.userHealthTargets?.weight) return null
  if (authStore?.user?.units === 'metric')
    return `${props.userHealthTargets.weight} ${t('generalItems.unitsKg')}`
  return `${kgToLbs(props.userHealthTargets.weight)} ${t('generalItems.unitsLbs')}`
})
const weightArrowDirection = computed(() => {
  if (!props.userHealthTargets?.weight || !currentWeight.value) return null
  return currentWeight.value > props.userHealthTargets.weight ? 'down' : 'up'
})

// BMI computed properties
const bmiDisplay = computed(() => (currentBMI.value ? String(currentBMI.value) : null))
const bmiFooterText = computed(() => {
  if (currentBMI.value) return bmiDescription.value
  if (currentWeight.value) return t('healthDashboardZoneComponent.noHeightDefined')
  return t('healthDashboardZoneComponent.noWeightData')
})

// Steps computed properties
const stepsDisplay = computed(() => (todaySteps.value ? String(todaySteps.value) : null))
const stepsTargetDisplay = computed(() => {
  if (!props.userHealthTargets?.steps) return null
  return `${props.userHealthTargets.steps} ${t('healthDashboardZoneComponent.stepsTargetLabel')}`
})
const stepsArrowDirection = computed(() => {
  if (!props.userHealthTargets?.steps) return null
  return todaySteps.value < props.userHealthTargets.steps ? 'down' : 'up'
})

// Fasting computed properties
const fastingDisplay = computed(() =>
  activeFasting.value ? formatSecondsToHoursMinutes(activeFastingElapsed.value) : null
)
const fastingSubtitle = computed(() =>
  activeFasting.value ? activeFasting.value.fasting_type : null
)
const fastingTargetDisplay = computed(() =>
  props.userHealthTargets?.fasting
    ? formatSecondsToHoursMinutes(props.userHealthTargets.fasting)
    : null
)
const fastingArrowDirection = computed(() => {
  if (!props.userHealthTargets?.fasting || !activeFasting.value) return null
  return activeFastingElapsed.value < props.userHealthTargets.fasting ? 'down' : 'up'
})

onMounted(async () => {
  try {
    isLoading.value = true
    healthDashboardData.value = await health.getUserDailyHealthStats()

    // Process steps data
    todaySteps.value = healthDashboardData.value.steps?.steps
      ? healthDashboardData.value.steps.steps
      : null
    // Process sleep data
    todaySleep.value = healthDashboardData.value.sleep?.total_sleep_seconds
      ? healthDashboardData.value.sleep.total_sleep_seconds
      : null
    restingHeartRate.value = healthDashboardData.value.sleep?.resting_heart_rate
      ? healthDashboardData.value.sleep.resting_heart_rate
      : null
    hrvStatus.value = healthDashboardData.value.sleep?.hrv_status
      ? healthDashboardData.value.sleep.hrv_status
      : null
    avgSkinTempDeviation.value = healthDashboardData.value.sleep?.avg_skin_temp_deviation
      ? healthDashboardData.value.sleep.avg_skin_temp_deviation
      : null
    // Process weight data
    if (healthDashboardData.value.weight?.weight) {
      currentWeight.value = healthDashboardData.value.weight.weight
      if (healthDashboardData.value.weight.bmi) {
        currentBMI.value = healthDashboardData.value.weight.bmi.toFixed(2)
      }

      if (currentBMI.value) {
        if (currentBMI.value < 18.5) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiUnderweight')
        } else if (currentBMI.value >= 18.5 && currentBMI.value < 24.9) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiNormalWeight')
        } else if (currentBMI.value >= 25 && currentBMI.value < 29.9) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiOverweight')
        } else if (currentBMI.value >= 30 && currentBMI.value < 34.9) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiObesityClass1')
        } else if (currentBMI.value >= 35 && currentBMI.value < 39.9) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiObesityClass2')
        } else if (currentBMI.value >= 40) {
          bmiDescription.value = t('healthDashboardZoneComponent.bmiObesityClass3')
        }
      }
    }
    // Process fasting data
    if (healthDashboardData.value.fasting) {
      activeFasting.value = healthDashboardData.value.fasting
      if (activeFasting.value.status === 'in_progress' && activeFasting.value.fast_start_time) {
        const startTime = new Date(activeFasting.value.fast_start_time).getTime()
        const now = Date.now()
        activeFastingElapsed.value = Math.floor((now - startTime) / 1000)
      } else if (activeFasting.value.actual_duration_seconds) {
        activeFastingElapsed.value = activeFasting.value.actual_duration_seconds
      }
    }
  } catch (error) {
    push.error(`${t('healthDashboardZoneComponent.errorFetchingHealthDailyStats')} - ${error}`)
  } finally {
    isLoading.value = false
  }
})
</script>
