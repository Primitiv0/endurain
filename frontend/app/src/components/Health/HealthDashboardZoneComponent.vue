<template>
  <div class="col">
    <div class="row">
      <!-- Today's sleep -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.sleep') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="todaySleep">{{ formatSecondsToHoursMinutes(todaySleep) }}</h1>
            <h1 v-else>{{ $t('generalItems.labelNoData') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <span v-if="userHealthTargets && userHealthTargets['sleep']">
              <font-awesome-icon
                :icon="['fas', 'angle-down']"
                class="me-1"
                v-if="todaySleep < userHealthTargets.sleep"
              />
              <font-awesome-icon :icon="['fas', 'angle-up']" class="me-1" v-else />
              {{ formatSecondsToHoursMinutes(userHealthTargets.sleep) }}
            </span>
            <span v-else>{{ $t('healthDashboardZoneComponent.noSleepTarget') }}</span>
          </div>
        </div>
      </div>
      <!-- resting heart rate -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.restingHeartRate') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="restingHeartRate">
              {{ restingHeartRate }} {{ $t('generalItems.unitsBpm') }}
            </h1>
            <h1 v-else>{{ $t('generalItems.labelNoData') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <span v-if="hrvStatus">{{ $t(getHrvStatusI18nKey(hrvStatus)) }}</span>
            <span v-else>{{ $t('generalItems.labelNoData') }}</span>
          </div>
        </div>
      </div>
      <!-- avg skin temperature deviation -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.avgSkinTemperatureDeviation') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="avgSkinTempDeviation">
              {{ avgSkinTempDeviation }} {{ $t('generalItems.unitsCelsius') }}
            </h1>
            <h1 v-else>{{ $t('generalItems.labelNoData') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <span>{{ $t('generalItems.labelNoData') }}</span>
          </div>
        </div>
      </div>
      <!-- weight -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.weight') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="currentWeight && authStore?.user?.units === 'metric'">
              {{ currentWeight }} {{ $t('generalItems.unitsKg') }}
            </h1>
            <h1 v-else-if="currentWeight && authStore.user.units === 'imperial'">
              {{ kgToLbs(currentWeight) }} {{ $t('generalItems.unitsLbs') }}
            </h1>
            <h1 v-else>{{ $t('generalItems.labelNotApplicable') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <font-awesome-icon
              :icon="['fas', 'angle-down']"
              class="me-1"
              v-if="userHealthTargets && currentWeight && currentWeight > userHealthTargets.weight"
            />
            <font-awesome-icon
              :icon="['fas', 'angle-up']"
              class="me-1"
              v-else-if="
                userHealthTargets && currentWeight && currentWeight <= userHealthTargets.weight
              "
            />
            <span
              v-if="
                userHealthTargets &&
                userHealthTargets['weight'] &&
                authStore?.user?.units === 'metric'
              "
            >
              {{ userHealthTargets.weight }} {{ $t('generalItems.unitsKg') }}
            </span>
            <span
              v-else-if="
                userHealthTargets &&
                userHealthTargets['weight'] &&
                authStore?.user?.units === 'imperial'
              "
            >
              {{ kgToLbs(userHealthTargets.weight) }} {{ $t('generalItems.unitsLbs') }}
            </span>
            <span v-else>{{ $t('healthDashboardZoneComponent.noWeightTarget') }}</span>
          </div>
        </div>
      </div>
      <!-- BMI -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.bmi') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="currentBMI">{{ currentBMI }}</h1>
            <h1 v-else>{{ $t('generalItems.labelNotApplicable') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <span v-if="currentBMI">{{ bmiDescription }}</span>
            <span v-else-if="!currentBMI && currentWeight">{{
              $t('healthDashboardZoneComponent.noHeightDefined')
            }}</span>
            <span v-else>{{ $t('healthDashboardZoneComponent.noWeightData') }}</span>
          </div>
        </div>
      </div>
      <!-- Today's steps -->
      <div class="col-lg-4 col-md-12">
        <div class="card mb-3 text-center shadow-sm">
          <div class="card-header">
            <h4>{{ $t('healthDashboardZoneComponent.steps') }}</h4>
          </div>
          <div class="card-body">
            <h1 v-if="todaySteps">{{ todaySteps }}</h1>
            <h1 v-else>{{ $t('generalItems.labelNotApplicable') }}</h1>
          </div>
          <div class="card-footer text-body-secondary">
            <span v-if="userHealthTargets && userHealthTargets['steps']">
              <font-awesome-icon
                :icon="['fas', 'angle-down']"
                class="me-1"
                v-if="todaySteps < userHealthTargets.steps"
              />
              <font-awesome-icon :icon="['fas', 'angle-up']" class="me-1" v-else />
              {{ userHealthTargets.steps }}
              {{ $t('healthDashboardZoneComponent.stepsTargetLabel') }}
            </span>
            <span v-else>{{ $t('healthDashboardZoneComponent.noStepsTarget') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
// Importing the stores
import { useAuthStore } from '@/stores/authStore'
import { kgToLbs } from '@/utils/unitsUtils'
import { formatSecondsToHoursMinutes } from '@/utils/dateTimeUtils'
import { getHrvStatusI18nKey } from '@/utils/healthUtils'
//
import { health } from '@/services/healthService'

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

onMounted(async () => {
  try {
    isLoading.value = true
    healthDashboardData.value = await health.getUserDailyHealthStats()
    console.log('Health Dashboard Data:', healthDashboardData.value)

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
    // Process fasting data (if needed)
  } catch (error) {
    push.error(`${t('healthDashboardZoneComponent.errorFetchingHealthDailyStats')} - ${error}`)
  } finally {
    isLoading.value = false
  }
})
</script>
