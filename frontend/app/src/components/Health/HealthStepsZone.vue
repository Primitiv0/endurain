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

      <BarChartPlaceholderComponent
        class="mt-3"
        :number-of-bars="7"
        v-if="isLoadingParent || isLoading"
      />
      <!-- Checking if userHealthStepsPagination is loaded and has length -->
      <!-- show graph -->
      <HealthStepsBarChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthSteps="userHealthStepsPagination"
        :isLoading="isLoading"
        v-else-if="userHealthStepsPagination && userHealthStepsPagination.length"
      />

      <div class="row row-gap-3 mt-3 align-items-center">
        <div class="col-sm-7">
          <div class="placeholder-glow" v-if="isLoadingParent || isLoading">
            <span class="placeholder col-8 bg-secondary rounded"></span>
          </div>
          <span v-else>
            {{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps1') }}{{ userHealthStepsNumber
            }}{{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps2')
            }}{{ userHealthStepsPagination.length
            }}{{ $t('healthStepsZoneComponent.labelNumberOfHealthSteps3') }}
          </span>
        </div>

        <div class="col">
          <form class="d-flex">
            <select
              class="form-select"
              :disabled="isLoadingParent || isLoading"
              v-model="intervalFilter"
            >
              <option value="last_7_days">{{ $t('healthView.filter_last_7_days') }}</option>
              <option value="last_30_days">{{ $t('healthView.filter_last_30_days') }}</option>
              <option value="last_90_days">{{ $t('healthView.filter_last_90_days') }}</option>
              <option value="last_year">{{ $t('healthView.filter_last_year') }}</option>
              <option value="all_time">{{ $t('healthView.filter_all_time') }}</option>
            </select>

            <select
              class="form-select ms-2"
              :disabled="isLoadingParent || isLoading"
              v-model="paginationFilter"
            >
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

      <!-- Displaying loading new steps if applicable -->
      <ListPlaceholderComponent class="mt-3" :numberOfRows="1" v-if="isLoadingNewSteps" />

      <ListPlaceholderComponent
        class="mt-3"
        :numberOfRows="5"
        v-if="isLoadingParent || isLoading"
      />
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
          v-if="paginationFilter !== 'disabled'"
        />
      </div>
      <!-- Displaying a message or component when there are no weight measurements -->
      <NoItemsFoundComponent class="mt-3" :show-shadow="false" v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import HealthStepsAddEditModalComponent from './HealthStepsZone/HealthStepsAddEditModalComponent.vue'
import HealthStepsBarChartComponent from './HealthStepsZone/HealthStepsBarChartComponent.vue'
import HealthStepsListComponent from './HealthStepsZone/HealthStepsListComponent.vue'
import BarChartPlaceholderComponent from '../PlaceholderComponents/BarChartPlaceholderComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
import ModalComponentNumberInput from '../Modals/ModalComponentNumberInput.vue'
import ListPlaceholderComponent from '../PlaceholderComponents/ListPlaceholderComponent.vue'
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
const userHealthStepsPagination = ref([])
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

async function updateHealthStepsPagination() {
  try {
    isLoading.value = true
    const stepsDataPagination = await health_steps.getUserHealthStepsWithPagination(
      pageNumber.value,
      numRecords.value,
      paginationFilter.value,
      intervalFilter.value
    )
    userHealthStepsPagination.value = stepsDataPagination.records
    userHealthStepsNumber.value = stepsDataPagination.total
    totalPages.value = Math.ceil(userHealthStepsNumber.value / numRecords.value)
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
  userHealthStepsNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetStepsTarget(stepsTarget) {
  emit('setStepsTarget', stepsTarget)
}

function handleFilterChange() {
  pageNumber.value = 1
  updateHealthStepsPagination()
}

watch(pageNumber, updateHealthStepsPagination, { immediate: false })
watch([intervalFilter, paginationFilter], handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthStepsPagination()
})
</script>
