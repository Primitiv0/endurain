<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <!-- Active fasting zone -->
      <div v-if="activeFasting" class="card mb-3 border-primary">
        <div class="card-header bg-primary text-white d-flex justify-content-between">
          <h5 class="mb-0">
            <font-awesome-icon :icon="['fas', 'clock']" class="me-2" />
            {{ $t('healthFastingZoneComponent.activeFasting') }}
          </h5>
          <span class="badge bg-light text-primary">
            {{ activeFasting.fasting_type }}
          </span>
        </div>
        <div class="card-body text-center">
          <h2 class="display-4">{{ formatElapsedTime }}</h2>
          <p class="text-muted mb-2">
            {{ $t('healthFastingZoneComponent.started') }}:
            {{ formatTime(activeFasting.fast_start_time) }}
          </p>
          <div class="progress mb-3" style="height: 20px">
            <div
              class="progress-bar bg-success"
              role="progressbar"
              :style="{ width: progressPercentage + '%' }"
              :aria-valuenow="progressPercentage"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              {{ progressPercentage }}%
            </div>
          </div>
          <div class="d-flex justify-content-center gap-2">
            <button
              class="btn btn-success"
              @click="completeFasting('completed')"
              :disabled="isCompletingFast || progressPercentage < 100"
            >
              <font-awesome-icon :icon="['fas', 'check']" class="me-1" />
              {{ $t('healthFastingZoneComponent.buttonComplete') }}
            </button>
            <button
              class="btn btn-warning"
              @click="completeFasting('broken')"
              :disabled="isCompletingFast"
            >
              <font-awesome-icon :icon="['fas', 'xmark']" class="me-1" />
              {{ $t('healthFastingZoneComponent.buttonBreak') }}
            </button>
            <button
              class="btn btn-secondary"
              @click="completeFasting('cancelled')"
              :disabled="isCompletingFast"
            >
              <font-awesome-icon :icon="['fas', 'ban']" class="me-1" />
              {{ $t('healthFastingZoneComponent.buttonCancel') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Start fasting button (only when no active fast) -->
      <div class="d-flex" v-if="!activeFasting">
        <a
          class="w-100 btn btn-primary shadow-sm me-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addFastingModal"
        >
          <font-awesome-icon :icon="['fas', 'play']" class="me-1" />
          {{ $t('healthFastingZoneComponent.buttonStartFasting') }}
        </a>
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addFastingTargetModal"
        >
          <font-awesome-icon :icon="['fas', 'bullseye']" class="me-1" />
          {{ $t('healthFastingZoneComponent.buttonFastingTarget') }}
        </a>
      </div>

      <HealthFastingAddEditModalComponent
        :action="'add'"
        @isLoadingNewFasting="updateIsLoadingNewFasting"
        @createdFasting="updateFastingListAdded"
      />

      <ModalComponentHoursMinutesInput
        modalId="addFastingTargetModal"
        :title="t('healthFastingZoneComponent.buttonFastingTarget')"
        :hoursFieldLabel="t('generalItems.labelHoursShort')"
        :minutesFieldLabel="t('generalItems.labelMinutesShort')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :secondsDefaultValue="props.userHealthTargets?.fasting || 57600"
        @fieldsToEmitAction="submitSetFastingTarget"
      />

      <!-- Stats cards -->
      <div class="row mt-3" v-if="fastingStats">
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.totalFasts') }}
              </h6>
              <h4 class="card-title">{{ fastingStats.total_fasts }}</h4>
            </div>
          </div>
        </div>
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.currentStreak') }}
              </h6>
              <h4 class="card-title">
                {{ fastingStats.current_streak }}
                {{ $t('healthFastingZoneComponent.days') }}
              </h4>
            </div>
          </div>
        </div>
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.longestStreak') }}
              </h6>
              <h4 class="card-title">
                {{ fastingStats.longest_streak }}
                {{ $t('healthFastingZoneComponent.days') }}
              </h4>
            </div>
          </div>
        </div>
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.avgDuration') }}
              </h6>
              <h4 class="card-title">
                {{ formatSecondsToHoursMinutesSeconds(fastingStats.avg_duration_seconds) }}
              </h4>
            </div>
          </div>
        </div>
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.totalFastingTime') }}
              </h6>
              <h4 class="card-title">
                {{ formatSecondsToHoursMinutesSeconds(fastingStats.total_fasting_seconds) }}
              </h4>
            </div>
          </div>
        </div>
        <div class="col-md-4 col-sm-6 mb-2">
          <div class="card text-center h-100">
            <div class="card-body">
              <h6 class="card-subtitle mb-2 text-muted">
                {{ $t('healthFastingZoneComponent.completionRate') }}
              </h6>
              <h4 class="card-title">{{ fastingStats.completion_rate }}%</h4>
            </div>
          </div>
        </div>
      </div>

      <div class="row row-gap-3 mt-3 align-items-center">
        <div class="col-sm-7">
          <span>
            {{ $t('healthFastingZoneComponent.labelNumberOfHealthFasting1')
            }}{{ userHealthFastingNumber
            }}{{ $t('healthFastingZoneComponent.labelNumberOfHealthFasting2')
            }}{{ userHealthFastingPagination.length
            }}{{ $t('healthFastingZoneComponent.labelNumberOfHealthFasting3') }}
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

      <!-- Displaying loading new fasting if applicable -->
      <ul class="mt-3 list-group list-group-flush" v-if="isLoadingNewFasting">
        <li class="list-group-item rounded">
          <LoadingComponent />
        </li>
      </ul>

      <LoadingComponent class="mt-3" v-if="isLoadingParent || isLoading" />
      <div
        v-else-if="userHealthFastingPagination && userHealthFastingPagination.length"
        class="mt-3"
      >
        <!-- list zone -->
        <ul
          class="my-3 list-group list-group-flush"
          v-for="userHealthFasting in userHealthFastingPagination"
          :key="userHealthFasting.id"
          :userHealthFasting="userHealthFasting"
        >
          <HealthFastingListComponent
            :userHealthFasting="userHealthFasting"
            @deletedFasting="updateFastingListDeleted"
            @editedFasting="updateFastingListEdited"
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
      <!-- Displaying a message or component when there are no fasting records -->
      <NoItemsFoundComponent class="mt-3" :show-shadow="false" v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'

import HealthFastingAddEditModalComponent from './HealthFastingZone/HealthFastingAddEditModalComponent.vue'
import HealthFastingListComponent from './HealthFastingZone/HealthFastingListComponent.vue'
import ModalComponentHoursMinutesInput from '../Modals/ModalComponentHoursMinutesInput.vue'
import LoadingComponent from '../GeneralComponents/LoadingComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'

import { health_fasting } from '@/services/health_fastingService'
import { useServerSettingsStore } from '@/stores/serverSettingsStore'
import { formatTime, formatSecondsToHoursMinutesSeconds } from '@/utils/dateTimeUtils'

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

const emit = defineEmits(['setFastingTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewFasting = ref(false)
const isLoading = ref(false)
const isCompletingFast = ref(false)
const userHealthFastingNumber = ref(0)
const userHealthFastingPagination = ref([])
const activeFasting = ref(null)
const fastingStats = ref(null)
const pageNumber = ref(1)
const totalPages = ref(1)
const elapsedSeconds = ref(0)
let timerInterval = null
const numRecords = computed(() => {
  if (paginationFilter.value === 'disabled') {
    return serverSettingsStore.serverSettings.num_records_per_page || 25
  }
  return parseInt(paginationFilter.value)
})
const paginationFilter = ref('disabled')
const intervalFilter = ref('last_7_days')

const formatElapsedTime = computed(() => {
  const hours = Math.floor(elapsedSeconds.value / 3600)
  const minutes = Math.floor((elapsedSeconds.value % 3600) / 60)
  const seconds = elapsedSeconds.value % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

const progressPercentage = computed(() => {
  if (!activeFasting.value || !activeFasting.value.target_duration_seconds) {
    return 0
  }
  const percentage = (elapsedSeconds.value / activeFasting.value.target_duration_seconds) * 100
  return Math.min(Math.round(percentage), 100)
})

function startTimer() {
  if (timerInterval) clearInterval(timerInterval)
  if (activeFasting.value && activeFasting.value.fast_start_time) {
    const startTime = new Date(activeFasting.value.fast_start_time).getTime()
    timerInterval = setInterval(() => {
      elapsedSeconds.value = Math.floor((Date.now() - startTime) / 1000)
    }, 1000)
    // Initialize immediately
    elapsedSeconds.value = Math.floor((Date.now() - startTime) / 1000)
  }
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

async function fetchActiveFasting() {
  try {
    activeFasting.value = await health_fasting.getActiveFasting()
    if (activeFasting.value) {
      startTimer()
    }
  } catch (error) {
    push.error(`${t('healthFastingZoneComponent.errorFetchingActiveFasting')} - ${error}`)
  }
}

async function fetchFastingStats() {
  try {
    fastingStats.value = await health_fasting.getFastingStats()
  } catch (error) {
    push.error(`${t('healthFastingZoneComponent.errorFetchingFastingStats')} - ${error}`)
  }
}

async function completeFasting(status) {
  if (!activeFasting.value) return

  try {
    isCompletingFast.value = true
    const data = {
      fast_end_time: new Date().toISOString(),
      status: status
    }
    await health_fasting.completeHealthFasting(activeFasting.value.id, data)
    stopTimer()

    // Refresh data
    activeFasting.value = null
    await fetchFastingStats()
    await updateHealthFastingPagination()

    push.success(t('healthFastingZoneComponent.successCompleteFasting'))
  } catch (error) {
    push.error(`${t('healthFastingZoneComponent.errorCompleteFasting')} - ${error}`)
  } finally {
    isCompletingFast.value = false
  }
}

async function updateHealthFastingPagination() {
  try {
    isLoading.value = true
    const fastingDataPagination = await health_fasting.getUserHealthFastingWithPagination(
      pageNumber.value,
      numRecords.value,
      paginationFilter.value,
      intervalFilter.value
    )
    userHealthFastingPagination.value = fastingDataPagination.records
    userHealthFastingNumber.value = fastingDataPagination.total
    totalPages.value = Math.ceil(userHealthFastingNumber.value / numRecords.value)
  } catch (error) {
    push.error(`${t('healthFastingZoneComponent.errorFetchingHealthFasting')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function updateIsLoadingNewFasting(isLoadingNewFastingNewValue) {
  isLoadingNewFasting.value = isLoadingNewFastingNewValue
}

function updateFastingListAdded(createdFasting) {
  const updateOrAdd = (array, newEntry) => {
    const index = array.findIndex((item) => item.id === newEntry.id)
    if (index !== -1) {
      array[index] = newEntry
    } else {
      array.unshift(newEntry)
      userHealthFastingNumber.value++
    }
  }
  isLoadingNewFasting.value = true
  if (userHealthFastingPagination.value) {
    updateOrAdd(userHealthFastingPagination.value, createdFasting)
  }
  // If status is in_progress, set as active
  if (createdFasting.status === 'in_progress') {
    activeFasting.value = createdFasting
    startTimer()
  }
  isLoadingNewFasting.value = false
}

function updateFastingListDeleted(deletedFastingId) {
  // Check if the deleted fasting was the active one
  if (activeFasting.value && activeFasting.value.id === deletedFastingId) {
    stopTimer()
    activeFasting.value = null
  }

  if (userHealthFastingPagination.value) {
    userHealthFastingPagination.value = userHealthFastingPagination.value.filter(
      (fasting) => fasting.id !== deletedFastingId
    )
    userHealthFastingNumber.value--
  }
}

function updateFastingListEdited(editedFasting) {
  if (userHealthFastingPagination.value) {
    const index = userHealthFastingPagination.value.findIndex(
      (fasting) => fasting.id === editedFasting.id
    )
    if (index !== -1) {
      userHealthFastingPagination.value[index] = editedFasting
    }
  }
}

function setPageNumber(newPageNumber) {
  pageNumber.value = newPageNumber
}

function submitSetFastingTarget(fastingTarget) {
  emit('setFastingTarget', fastingTarget)
}

watch([pageNumber, paginationFilter, intervalFilter], () => {
  updateHealthFastingPagination()
})

onMounted(async () => {
  await fetchActiveFasting()
  await fetchFastingStats()
  await updateHealthFastingPagination()
})

onUnmounted(() => {
  stopTimer()
})
</script>
