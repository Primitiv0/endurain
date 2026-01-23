<template>
  <h1>{{ $t('healthView.title') }}</h1>
  <div class="row row-gap-3">
    <!-- Include the HealthSideBarComponent -->
    <HealthSideBarComponent
      :activeSection="activeSection"
      @updateActiveSection="updateActiveSection"
    />

    <LoadingComponent v-if="isLoading" />

    <!-- Include the HealthDashboardZone
    <HealthDashboardZone :userHealthTargets="userHealthTargets" :isLoadingParent="isLoading"
      v-if="activeSection === 'dashboard' && !isLoading" /> -->

    <!-- Include the HealthSleepZone -->
    <HealthSleepZone
      :userHealthTargets="userHealthTargets"
      :isLoadingParent="isLoading"
      @setSleepTarget="setSleepTarget"
      v-if="activeSection === 'sleep' && !isLoading"
    />

    <!-- Include the HealthRHRZone -->
    <HealthRHRZone :isLoadingParent="isLoading" v-if="activeSection === 'rhr' && !isLoading" />

    <!-- Include the HealthStepsZone -->
    <HealthStepsZone
      :userHealthTargets="userHealthTargets"
      :isLoadingParent="isLoading"
      @setStepsTarget="setStepsTarget"
      v-if="activeSection === 'steps' && !isLoading"
    />

    <!-- Include the HealthWeightZone -->
    <HealthWeightZone
      :userHealthTargets="userHealthTargets"
      :isLoadingParent="isLoading"
      @setWeightTarget="setWeightTarget"
      v-if="activeSection === 'weight' && !isLoading"
    />
  </div>
  <!-- back button -->
  <BackButtonComponent />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import HealthSideBarComponent from '../components/Health/HealthSideBarComponent.vue'
import HealthDashboardZone from '../components/Health/HealthDashboardZoneComponent.vue'
import HealthSleepZone from '../components/Health/HealthSleepZone.vue'
import HealthRHRZone from '@/components/Health/HealthRHRZone.vue'
import HealthStepsZone from '../components/Health/HealthStepsZone.vue'
import HealthWeightZone from '../components/Health/HealthWeightZone.vue'
import BackButtonComponent from '@/components/GeneralComponents/BackButtonComponent.vue'
import LoadingComponent from '@/components/GeneralComponents/LoadingComponent.vue'
import { health_targets } from '@/services/health_targetsService'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const activeSection = ref('dashboard')
const isLoading = ref(false)
// Targets variables
const userHealthTargets = ref(null)

function updateActiveSection(section) {
  activeSection.value = section
  router.push({ query: { tab: section } })
}

// Health Targets functions
async function fetchHealthTargets() {
  try {
    isLoading.value = true
    userHealthTargets.value = await health_targets.getUserHealthTargets()
  } catch (error) {
    push.error(`${t('healthView.errorFetchingHealthTargets')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function setWeightTarget(weightTarget) {
  const data = {
    id: userHealthTargets.value.id,
    user_id: userHealthTargets.value.user_id,
    weight: weightTarget
  }
  try {
    health_targets.setUserHealthTargets(data)
    userHealthTargets.value.weight = weightTarget
    push.success(t('healthView.successUpdatingWeightTarget'))
  } catch (error) {
    push.error(`${t('healthView.errorUpdatingWeightTarget')} - ${error}`)
  }
}

function setStepsTarget(stepsTarget) {
  const data = {
    id: userHealthTargets.value.id,
    user_id: userHealthTargets.value.user_id,
    steps: stepsTarget
  }
  try {
    health_targets.setUserHealthTargets(data)
    userHealthTargets.value.steps = stepsTarget
    push.success(t('healthView.successUpdatingStepsTarget'))
  } catch (error) {
    push.error(`${t('healthView.errorUpdatingStepsTarget')} - ${error}`)
  }
}

function setSleepTarget(sleepTarget) {
  const data = {
    id: userHealthTargets.value.id,
    user_id: userHealthTargets.value.user_id,
    sleep: sleepTarget
  }
  try {
    health_targets.setUserHealthTargets(data)
    userHealthTargets.value.sleep = sleepTarget
    push.success(t('healthView.successUpdatingSleepTarget'))
  } catch (error) {
    push.error(`${t('healthView.errorUpdatingSleepTarget')} - ${error}`)
  }
}

onMounted(async () => {
  if (route.query.tab && typeof route.query.tab === 'string') {
    activeSection.value = route.query.tab
  }
  await fetchHealthTargets()
})
</script>
