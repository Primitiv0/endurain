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

      <div class="row row-gap-3 mt-3 align-items-center">
        <div class="col-sm-7">
          <span>
            {{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR1') }}{{ userHealthSleepNumber
            }}{{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR2')
            }}{{ userHealthSleepPagination.length
            }}{{ $t('healthRHRZoneComponent.labelNumberOfHealthRHR3') }}
          </span>
        </div>

        <div class="col">
          <form class="d-flex">
            <select class="form-select" v-model="intervalFilter">
              <option value="last_7_days">{{ $t('healthView.filter_last_7_days') }}</option>
              <option value="last_30_days">{{ $t('healthView.filter_last_30_days') }}</option>
              <option value="last_90_days">{{ $t('healthView.filter_last_90_days') }}</option>
              <option value="last_year">{{ $t('healthView.filter_last_year') }}</option>
              <option value="all_time">{{ $t('healthView.filter_all_time') }}</option>
            </select>

            <select class="form-select ms-2" v-model="paginationFilter">
              <option value="disabled">{{ $t('healthView.paginationDisabled') }}</option>
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </form>
        </div>
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
          v-if="paginationFilter !== 'disabled'"
        />
      </div>
      <!-- Displaying a message or component when there are no RHR measurements -->
      <NoItemsFoundComponent class="mt-3" :show-shadow="false" v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
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
const numRecords = computed(() => {
  if (paginationFilter.value === 'disabled') {
    return serverSettingsStore.serverSettings.num_records_per_page || 25
  }
  return parseInt(paginationFilter.value)
})
const paginationFilter = ref('disabled')
const intervalFilter = ref('last_7_days')

async function updateHealthSleepPagination() {
  try {
    isLoading.value = true
    const sleepDataPagination = await health_sleep.getUserHealthSleepWithPagination(
      pageNumber.value,
      numRecords.value,
      paginationFilter.value,
      intervalFilter.value
    )
    userHealthSleepPagination.value = sleepDataPagination.records
    userHealthSleepNumber.value = sleepDataPagination.total
    totalPages.value = Math.ceil(userHealthSleepNumber.value / numRecords.value)
  } catch (error) {
    push.error(`${t('healthSleepZoneComponent.errorFetchingHealthSleep')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function setPageNumber(page) {
  pageNumber.value = page
}

function handleFilterChange() {
  pageNumber.value = 1
  updateHealthSleepPagination()
}

watch(pageNumber, updateHealthSleepPagination, { immediate: false })
watch([intervalFilter, paginationFilter], handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthSleepPagination()
})
</script>
