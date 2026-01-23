<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <!-- add sleep button -->
      <div class="d-flex">
        <a
          class="w-100 btn btn-primary shadow-sm me-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addSleepModal"
          >{{ t('healthSleepZoneComponent.buttonAddSleep') }}</a
        >
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addSleepTargetModal"
          >{{ $t('healthSleepZoneComponent.buttonSleepTarget') }}</a
        >
      </div>

      <HealthSleepAddEditModalComponent
        :action="'add'"
        @isLoadingNewSleep="updateIsLoadingNewSleep"
        @createdSleep="updateSleepListAdded"
      />

      <ModalComponentHoursMinutesInput
        modalId="addSleepTargetModal"
        :title="t('healthSleepZoneComponent.buttonSleepTarget')"
        :hoursFieldLabel="t('healthSleepZoneComponent.modalSleepTargetHoursLabel')"
        :minutesFieldLabel="t('healthSleepZoneComponent.modalSleepTargetMinutesLabel')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :secondsDefaultValue="props.userHealthTargets?.sleep || 28800"
        @fieldsToEmitAction="submitSetSleepTarget"
      />

      <LoadingComponent class="mt-3" v-if="isLoadingParent || isLoading" />
      <!-- Checking if userHealthSleepPagination is loaded and has length -->
      <!-- show graph -->
      <HealthSleepBarChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthSleep="userHealthSleepPagination"
        :isLoading="isLoading"
        v-else-if="userHealthSleepPagination && userHealthSleepPagination.length"
      />

      <div class="d-flex align-items-center justify-content-between mt-3">
        <span>
          {{ $t('healthSleepZoneComponent.labelNumberOfHealthSleep1') }}{{ userHealthSleepNumber
          }}{{ $t('healthSleepZoneComponent.labelNumberOfHealthSleep2')
          }}{{ userHealthSleepPagination.length
          }}{{ $t('healthSleepZoneComponent.labelNumberOfHealthSleep3') }}
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

      <!-- Displaying loading new sleep if applicable -->
      <ul class="mt-3 list-group list-group-flush" v-if="isLoadingNewSleep">
        <li class="list-group-item rounded">
          <LoadingComponent />
        </li>
      </ul>

      <LoadingComponent class="mt-3" v-if="isLoadingParent || isLoading" />
      <div v-else-if="userHealthSleepPagination && userHealthSleepPagination.length" class="mt-3">
        <!-- list zone -->
        <ul
          class="my-3 list-group list-group-flush"
          v-for="userHealthSleep in userHealthSleepPagination"
          :key="userHealthSleep.id"
          :data="userHealthSleep"
        >
          <!--<HealthSleepTimelineChartComponent
              :data="userHealthSleep.sleep_stages"
            />-->
          <HealthSleepListComponent
            :userHealthSleep="userHealthSleep"
            @deletedSleep="updateSleepListDeleted"
            @editedSleep="updateSleepListEdited"
          />
        </ul>

        <!-- pagination area -->
        <PaginationComponent
          :totalPages="totalPages"
          :pageNumber="pageNumber"
          @pageNumberChanged="setPageNumber"
        />
      </div>
      <!-- Displaying a message or component when there are no weight measurements -->
      <NoItemsFoundComponent class="mt-3" :show-shadow="false" v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import HealthSleepAddEditModalComponent from './HealthSleepZone/HealthSleepAddEditModalComponent.vue'
import ModalComponentHoursMinutesInput from '../Modals/ModalComponentHoursMinutesInput.vue'
import HealthSleepBarChartComponent from './HealthSleepZone/HealthSleepBarChartComponent.vue'
import HealthSleepListComponent from './HealthSleepZone/HealthSleepListComponent.vue'
import LoadingComponent from '../GeneralComponents/LoadingComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
// import stores
import { health_sleep } from '@/services/health_sleepService'
import { useServerSettingsStore } from '@/stores/serverSettingsStore'

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

const emit = defineEmits(['setSleepTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewSleep = ref(false)
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

function updateIsLoadingNewSleep(isLoadingNewSleepNewValue) {
  isLoadingNewSleep.value = isLoadingNewSleepNewValue
}

function updateSleepListAdded(createdSleep) {
  const updateOrAdd = (array, newEntry) => {
    const index = array.findIndex((item) => item.id === newEntry.id)
    if (index !== -1) {
      array[index] = newEntry
    } else {
      array.unshift(newEntry)
      userHealthSleepNumber.value++
    }
  }
  isLoadingNewSleep.value = true
  if (userHealthSleepPagination.value) {
    updateOrAdd(userHealthSleepPagination.value, createdSleep)
  } else {
    userHealthSleepPagination.value = [createdSleep]
  }
  isLoadingNewSleep.value = false
}

function updateSleepListEdited(editedSleep) {
  const index = userHealthSleepPagination.value.findIndex((sleep) => sleep.id === editedSleep.id)
  userHealthSleepPagination.value[index] = editedSleep
}

function updateSleepListDeleted(deletedSleep) {
  userHealthSleepPagination.value = userHealthSleepPagination.value.filter(
    (sleep) => sleep.id !== deletedSleep
  )
  userHealthSleepNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetSleepTarget(sleepTarget) {
  emit('setSleepTarget', sleepTarget)
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
