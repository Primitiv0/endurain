<template>
  <h1>{{ $t('healthView.title') }}</h1>
  <div class="row row-gap-3">
    <!-- Include the HealthSideBarComponent -->
    <HealthSideBarComponent
      :activeSection="activeSection"
      @updateActiveSection="updateActiveSection"
    />

    <LoadingComponent v-if="isLoading" />

    <!-- Include the HealthDashboardZone -->
    <HealthDashboardZone
      :userHealthWeight="userHealthWeight"
      :userHealthSteps="userHealthSteps"
      :userHealthSleep="userHealthSleep"
      :userHealthTargets="userHealthTargets"
      v-if="activeSection === 'dashboard' && !isLoading"
    />

    <!-- Include the HealthSleepZone -->
    <HealthSleepZone
      :userHealthSleep="userHealthSleep"
      :userHealthSleepPagination="userHealthSleepPagination"
      :userHealthTargets="userHealthTargets"
      :isLoading="isLoading"
      :totalPages="totalPagesSleep"
      :pageNumber="pageNumberSleep"
      @createdSleep="updateSleepListAdded"
      @editedSleep="updateSleepListEdited"
      @deletedSleep="updateSleepListDeleted"
      @pageNumberChanged="setPageNumberSleep"
      @setSleepTarget="setSleepTarget"
      v-if="activeSection === 'sleep' && !isLoading"
    />

    <!-- Include the HealthRHRZone -->
    <HealthRHRZone
      :userHealthSleep="userHealthSleep"
      :userHealthSleepPagination="userHealthSleepPagination"
      :isLoading="isLoading"
      :totalPages="totalPagesRHR"
      :pageNumber="pageNumberRHR"
      @pageNumberChanged="setPageNumberRHR"
      v-if="activeSection === 'rhr' && !isLoading"
    />

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
import { ref, onMounted, watch } from 'vue'
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
import { health_sleep } from '@/services/health_sleepService'
import { health_targets } from '@/services/health_targetsService'
import { useServerSettingsStore } from '@/stores/serverSettingsStore'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const activeSection = ref('dashboard')
const isLoading = ref(true)
const numRecords = serverSettingsStore.serverSettings.num_records_per_page || 25
// Sleep variables
const isHealthSleepUpdatingLoading = ref(true)
const userHealthSleepNumber = ref(0)
const userHealthSleep = ref([])
const userHealthSleepPagination = ref([])
const pageNumberSleep = ref(1)
const totalPagesSleep = ref(1)
// RHR variables
const pageNumberRHR = ref(1)
const totalPagesRHR = ref(1)
// Targets variables
const userHealthTargets = ref(null)

function updateActiveSection(section) {
  activeSection.value = section
  router.push({ query: { tab: section } })
}

// Sleep functions
async function updateHealthSleepPagination() {
  try {
    isHealthSleepUpdatingLoading.value = true
    const sleepDataPagination = await health_sleep.getUserHealthSleepWithPagination(
      pageNumberSleep.value,
      numRecords
    )
    userHealthSleepPagination.value = sleepDataPagination.records
    isHealthSleepUpdatingLoading.value = false
  } catch (error) {
    push.error(`${t('healthView.errorFetchingHealthSleep')} - ${error}`)
  }
}

async function fetchHealthSleep() {
  try {
    const sleepData = await health_sleep.getUserHealthSleep()
    userHealthSleepNumber.value = sleepData.total
    userHealthSleep.value = sleepData.records
    await updateHealthSleepPagination()
    totalPagesSleep.value = Math.ceil(userHealthSleepNumber.value / numRecords)
  } catch (error) {
    push.error(`${t('healthView.errorFetchingHealthSleep')} - ${error}`)
  }
}

function updateSleepListAdded(createdSleep) {
  const updateOrAdd = (array, newEntry) => {
    const index = array.findIndex((item) => item.id === newEntry.id)
    if (index !== -1) {
      array[index] = newEntry
    } else {
      array.unshift(newEntry)
    }
  }
  if (userHealthSleepPagination.value) {
    updateOrAdd(userHealthSleepPagination.value, createdSleep)
  } else {
    userHealthSleepPagination.value = [createdSleep]
  }
  if (userHealthSleep.value) {
    updateOrAdd(userHealthSleep.value, createdSleep)
  } else {
    userHealthSleep.value = [createdSleep]
  }
  userHealthSleepNumber.value = userHealthSleep.value.length
}

function updateSleepListEdited(editedSleep) {
  const indexPagination = userHealthSleepPagination.value.findIndex(
    (sleep) => sleep.id === editedSleep.id
  )
  const index = userHealthSleep.value.findIndex((sleep) => sleep.id === editedSleep.id)
  userHealthSleepPagination.value[indexPagination] = editedSleep
  userHealthSleep.value[index] = editedSleep
}

function updateSleepListDeleted(deletedSleep) {
  userHealthSleepPagination.value = userHealthSleepPagination.value.filter(
    (sleep) => sleep.id !== deletedSleep
  )
  userHealthSleep.value = userHealthSleep.value.filter((sleep) => sleep.id !== deletedSleep)
  userHealthSleepNumber.value--
}

function setPageNumberSleep(page) {
  pageNumberSleep.value = page
}

// RHR functions
function setPageNumberRHR(page) {
  pageNumberRHR.value = page
}

// Health Targets functions
async function fetchHealthTargets() {
  try {
    userHealthTargets.value = await health_targets.getUserHealthTargets()
  } catch (error) {
    push.error(`${t('healthView.errorFetchingHealthTargets')} - ${error}`)
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

// Watch functions
watch(pageNumberSleep, updateHealthSleepPagination, { immediate: false })

onMounted(async () => {
  if (route.query.tab && typeof route.query.tab === 'string') {
    activeSection.value = route.query.tab
  }
  await fetchHealthSleep()
  await fetchHealthTargets()
  isHealthSleepUpdatingLoading.value = false
  isLoading.value = false
})
</script>
