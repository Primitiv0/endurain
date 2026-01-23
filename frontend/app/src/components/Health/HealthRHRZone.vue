<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <LoadingComponent v-if="isLoadingParent || isLoading" />
      <!-- show graph -->
      <HealthRHRLineChartComponent
        :userHealthSleep="userHealthSleepPagination"
        :isLoading="isLoading"
        v-if="userHealthSleepPagination && userHealthSleepPagination.length"
      />

      <div class="d-flex align-items-center justify-content-between mt-3">
        <span>
          {{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR1') }}{{ userHealthSleepNumber
          }}{{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR2')
          }}{{ userHealthSleepPagination.length
          }}{{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR3') }}
        </span>

        <form>
          <select class="form-select" v-model="sleepFilter">
            <option value="last_7_days">{{ $t('healthView.filter_last_7_days') }}</option>
            <option value="last_30_days">{{ $t('healthView.filter_last_30_days') }}</option>
            <option value="last_90_days">{{ $t('healthView.filter_last_90_days') }}</option>
            <option value="last_year">{{ $t('healthView.filter_last_year') }}</option>
            <option value="all_time">{{ $t('healthView.filter_all_time') }}</option>
          </select>
        </form>
      </div>

      <!-- Checking if userHealthSleep is loaded and has length -->
      <div v-if="userHealthSleepPagination && userHealthSleepPagination.length">
        <!-- list zone -->
        <ul
          class="my-3 list-group list-group-flush"
          v-for="userHealthSleep in userHealthSleepPagination"
          :key="userHealthSleep.id"
          :userHealthSleep="userHealthSleep"
        >
          <HealthRHRListComponent
            :userHealthSleep="userHealthSleep"
            v-if="userHealthSleep.resting_heart_rate"
          />
        </ul>

        <!-- pagination area -->
        <PaginationComponent
          :totalPages="totalPages"
          :pageNumber="pageNumber"
          @pageNumberChanged="setPageNumber"
        />
      </div>
      <!-- Displaying a message or component when there are no RHR measurements -->
      <div v-else>
        <NoItemsFoundComponent />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import HealthRHRLineChartComponent from './HealthRHRZone/HealthRHRLineChartComponent.vue'
import HealthRHRListComponent from './HealthRHRZone/HealthRHRListComponent.vue'
import LoadingComponent from '../GeneralComponents/LoadingComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
// import stores
import { health_sleep } from '@/services/health_sleepService'
import { useServerSettingsStore } from '@/stores/serverSettingsStore'

const props = defineProps({
  isLoadingParent: {
    type: Boolean,
    required: true
  }
})

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoading = ref(false)
const userHealthSleepNumber = ref(0)
const userHealthSleepPagination = ref([])
const pageNumber = ref(1)
const totalPages = ref(1)
const numRecords = serverSettingsStore.serverSettings.num_records_per_page || 25
const sleepFilter = ref('last_7_days')

async function updateHealthSleepPagination() {
  try {
    isLoading.value = true
    const sleepDataPagination = await health_sleep.getUserHealthSleepWithPagination(
      pageNumber.value,
      numRecords,
      sleepFilter.value
    )
    userHealthSleepPagination.value = sleepDataPagination.records
    userHealthSleepNumber.value = sleepDataPagination.total
    totalPages.value = Math.ceil(userHealthSleepNumber.value / numRecords)
  } catch (error) {
    push.error(`${t('healthSleepZoneComponent.errorFetchingHealthSleep')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function setPageNumber(page) {
  pageNumber.value = page
}

function handleFilterChange(newFilter) {
  pageNumber.value = 1
  updateHealthSleepPagination()
}

watch(pageNumber, updateHealthSleepPagination, { immediate: false })
watch(sleepFilter, handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthSleepPagination()
})
</script>
