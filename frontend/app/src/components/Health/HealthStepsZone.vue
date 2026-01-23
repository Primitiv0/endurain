<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <!-- add steps button -->
      <div class="d-flex">
        <a
          class="w-100 btn btn-primary shadow-sm me-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addStepsModal"
          >{{ $t('healthStepsZoneComponent.buttonAddSteps') }}</a
        >
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addStepsTargetModal"
          >{{ $t('healthStepsZoneComponent.buttonStepsTarget') }}</a
        >
      </div>

      <HealthStepsAddEditModalComponent
        :action="'add'"
        @isLoadingNewSteps="updateIsLoadingNewSteps"
        @createdSteps="updateStepsListAdded"
      />

      <ModalComponentNumberInput
        modalId="addStepsTargetModal"
        :title="t('healthStepsZoneComponent.buttonStepsTarget')"
        :numberFieldLabel="t('healthStepsZoneComponent.modalStepsTargetLabel')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :numberDefaultValue="props.userHealthTargets?.steps || parseInt(10000)"
        @numberToEmitAction="submitSetStepsTarget"
      />

      <LoadingComponent class="mt-3" v-if="isLoadingParent || isLoading" />
      <!-- Checking if userHealthStepsPagination is loaded and has length -->
      <!-- show graph -->
      <HealthStepsBarChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthSteps="userHealthStepsPagination"
        :isLoading="isLoading"
        v-else-if="userHealthStepsPagination && userHealthStepsPagination.length"
      />

      <div class="d-flex align-items-center justify-content-between mt-3">
        <span>
          {{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps1') }}{{ userHealthStepsNumber
          }}{{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps2')
          }}{{ userHealthStepsPagination.length
          }}{{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps3') }}
        </span>

        <form>
          <select class="form-select" v-model="stepsFilter">
            <option value="last_7_days">{{ $t('healthView.filter_last_7_days') }}</option>
            <option value="last_30_days">{{ $t('healthView.filter_last_30_days') }}</option>
            <option value="last_90_days">{{ $t('healthView.filter_last_90_days') }}</option>
            <option value="last_year">{{ $t('healthView.filter_last_year') }}</option>
            <option value="all_time">{{ $t('healthView.filter_all_time') }}</option>
          </select>
        </form>
      </div>

      <!-- Displaying loading new steps if applicable -->
      <ul class="mt-3 list-group list-group-flush" v-if="isLoadingNewSteps">
        <li class="list-group-item rounded">
          <LoadingComponent />
        </li>
      </ul>

      <LoadingComponent v-if="isLoadingParent || isLoading" />
      <!-- Checking if userHealthStepsPagination is loaded and has length -->
      <div v-else-if="userHealthStepsPagination && userHealthStepsPagination.length" class="mt-3">
        <!-- list zone -->
        <ul
          class="my-3 list-group list-group-flush"
          v-for="userHealthStep in userHealthStepsPagination"
          :key="userHealthStep.id"
          :userHealthStep="userHealthStep"
        >
          <HealthStepsListComponent
            :userHealthStep="userHealthStep"
            @deletedSteps="updateStepsListDeleted"
            @editedSteps="updateStepsListEdited"
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
import HealthStepsAddEditModalComponent from './HealthStepsZone/HealthStepsAddEditModalComponent.vue'
import HealthStepsBarChartComponent from './HealthStepsZone/HealthStepsBarChartComponent.vue'
import HealthStepsListComponent from './HealthStepsZone/HealthStepsListComponent.vue'
import LoadingComponent from '../GeneralComponents/LoadingComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
import ModalComponentNumberInput from '../Modals/ModalComponentNumberInput.vue'
// import stores
import { health_steps } from '@/services/health_stepsService'
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

const emit = defineEmits(['setStepsTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewSteps = ref(false)
const isLoading = ref(false)
const userHealthStepsNumber = ref(0)
const userHealthStepsPaginationNumber = ref(0)
const userHealthStepsPagination = ref([])
const pageNumber = ref(1)
const totalPages = ref(1)
const numRecords = serverSettingsStore.serverSettings.num_records_per_page || 25
const stepsFilter = ref('last_7_days')

async function updateHealthStepsPagination() {
  try {
    isLoading.value = true
    const stepsDataPagination = await health_steps.getUserHealthStepsWithPagination(
      pageNumber.value,
      numRecords,
      stepsFilter.value
    )
    userHealthStepsPagination.value = stepsDataPagination.records
    userHealthStepsNumber.value = stepsDataPagination.total
    userHealthStepsPaginationNumber.value = userHealthStepsPagination.value.length
    totalPages.value = Math.ceil(userHealthStepsNumber.value / numRecords)
  } catch (error) {
    push.error(`${t('healthStepsZoneComponent.errorFetchingHealthSteps')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function updateIsLoadingNewSteps(isLoadingNewStepsNewValue) {
  isLoadingNewSteps.value = isLoadingNewStepsNewValue
}

function updateStepsListAdded(createdStep) {
  const updateOrAdd = (array, newEntry) => {
    const index = array.findIndex((item) => item.id === newEntry.id)
    if (index !== -1) {
      array[index] = newEntry
    } else {
      array.unshift(newEntry)
      userHealthStepsPaginationNumber.value++
      userHealthStepsNumber.value++
    }
  }
  isLoadingNewSteps.value = true
  if (userHealthStepsPagination.value) {
    updateOrAdd(userHealthStepsPagination.value, createdStep)
  } else {
    userHealthStepsPagination.value = [createdStep]
  }
  isLoadingNewSteps.value = false
}

function updateStepsListEdited(editedStep) {
  const index = userHealthStepsPagination.value.findIndex((step) => step.id === editedStep.id)
  userHealthStepsPagination.value[index] = editedStep
}

function updateStepsListDeleted(deletedStep) {
  userHealthStepsPagination.value = userHealthStepsPagination.value.filter(
    (step) => step.id !== deletedStep
  )
  userHealthStepsPaginationNumber.value--
  userHealthStepsNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetStepsTarget(stepsTarget) {
  emit('setStepsTarget', stepsTarget)
}

function handleFilterChange(newFilter) {
  pageNumber.value = 1
  updateHealthStepsPagination()
}

watch(pageNumber, updateHealthStepsPagination, { immediate: false })
watch(stepsFilter, handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthStepsPagination()
})
</script>
