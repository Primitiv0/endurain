<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <!-- add weight button -->
      <div class="d-flex">
        <a
          class="w-100 btn btn-primary shadow-sm me-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addWeightModal"
          >{{ $t('healthWeightZoneComponent.buttonAddWeight') }}</a
        >
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addWeightTargetModal"
          >{{ $t('healthWeightZoneComponent.buttonWeightTarget') }}</a
        >
      </div>

      <HealthWeightAddEditModalComponent
        :action="'add'"
        @isLoadingNewWeight="updateIsLoadingNewWeight"
        @createdWeight="updateWeightListAdded"
      />

      <ModalComponentNumberInput
        modalId="addWeightTargetModal"
        :title="t('healthWeightZoneComponent.buttonWeightTarget')"
        :numberFieldLabel="t('healthWeightZoneComponent.modalWeightTargetLabel')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :numberDefaultValue="props.userHealthTargets?.weight || parseInt(70)"
        @numberToEmitAction="submitSetWeightTarget"
      />

      <LoadingComponent class="mt-3" v-if="isLoadingParent || isLoading" />
      <!-- Checking if userHealthWeightPagination is loaded and has length -->
      <!-- show graph -->
      <HealthWeightLineChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthWeight="userHealthWeightPagination"
        :isLoading="isLoading"
        v-else-if="userHealthWeightPagination && userHealthWeightPagination.length"
      />

      <div class="d-flex align-items-center justify-content-between mt-3">
        <span>
          {{ $t('healthWeightZoneComponent.labelNumberOfHealthWeightWeight1')
          }}{{ userHealthWeightNumber
          }}{{ $t('healthWeightZoneComponent.labelNumberOfHealthWeightWeight2')
          }}{{ userHealthWeightPagination.length
          }}{{ $t('healthWeightZoneComponent.labelNumberOfHealthWeightWeight3') }}
        </span>

        <form>
          <select class="form-select" v-model="weightFilter">
            <option value="last_7_days">{{ $t('healthView.filter_last_7_days') }}</option>
            <option value="last_30_days">{{ $t('healthView.filter_last_30_days') }}</option>
            <option value="last_90_days">{{ $t('healthView.filter_last_90_days') }}</option>
            <option value="last_year">{{ $t('healthView.filter_last_year') }}</option>
            <option value="all_time">{{ $t('healthView.filter_all_time') }}</option>
          </select>
        </form>
      </div>

      <!-- Displaying loading new weight if applicable -->
      <ul class="mt-3 list-group list-group-flush" v-if="isLoadingNewWeight">
        <li class="list-group-item rounded">
          <LoadingComponent />
        </li>
      </ul>

      <LoadingComponent v-if="isLoadingParent || isLoading" />
      <div v-else-if="userHealthWeightPagination && userHealthWeightPagination.length" class="mt-3">
        <!-- list zone -->
        <ul
          class="my-3 list-group list-group-flush"
          v-for="userHealthWeight in userHealthWeightPagination"
          :key="userHealthWeight.id"
          :userHealthWeight="userHealthWeight"
        >
          <HealthWeightListComponent
            :userHealthWeight="userHealthWeight"
            @deletedWeight="updateWeightListDeleted"
            @editedWeight="updateWeightListEdited"
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
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import HealthWeightAddEditModalComponent from './HealthWeightZone/HealthWeightAddEditModalComponent.vue'
import HealthWeightLineChartComponent from './HealthWeightZone/HealthWeightLineChartComponent.vue'
import HealthWeightListComponent from './HealthWeightZone/HealthWeightListComponent.vue'
import LoadingComponent from '../GeneralComponents/LoadingComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
import ModalComponentNumberInput from '../Modals/ModalComponentNumberInput.vue'
// import stores
import { health_weight } from '@/services/health_weightService'
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

const emit = defineEmits(['setWeightTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewWeight = ref(false)
const isLoading = ref(false)
const userHealthWeightNumber = ref(0)
const userHealthWeightPagination = ref([])
const pageNumber = ref(1)
const totalPages = ref(1)
const numRecords = serverSettingsStore.serverSettings.num_records_per_page || 25
const weightFilter = ref('last_7_days')

async function updateHealthWeightPagination() {
  try {
    isLoading.value = true
    const weightDataPagination = await health_weight.getUserHealthWeightWithPagination(
      pageNumber.value,
      numRecords,
      weightFilter.value
    )
    userHealthWeightPagination.value = weightDataPagination.records
    userHealthWeightNumber.value = weightDataPagination.total
    totalPages.value = Math.ceil(userHealthWeightNumber.value / numRecords)
  } catch (error) {
    push.error(`${t('healthWeightZoneComponent.errorFetchingHealthWeight')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function updateIsLoadingNewWeight(isLoadingNewWeightNewValue) {
  isLoadingNewWeight.value = isLoadingNewWeightNewValue
}

function updateWeightListAdded(createdWeight) {
  const updateOrAdd = (array, newEntry) => {
    const index = array.findIndex((item) => item.id === newEntry.id)
    if (index !== -1) {
      array[index] = newEntry
    } else {
      array.unshift(newEntry)
      userHealthWeightNumber.value++
    }
  }
  isLoadingNewWeight.value = true
  if (userHealthWeightPagination.value) {
    updateOrAdd(userHealthWeightPagination.value, createdWeight)
  } else {
    userHealthWeightPagination.value = [createdWeight]
  }
  isLoadingNewWeight.value = false
}

function updateWeightListEdited(editedWeight) {
  const index = userHealthWeightPagination.value.findIndex(
    (weight) => weight.id === editedWeight.id
  )
  userHealthWeightPagination.value[index] = editedWeight
}

function updateWeightListDeleted(deletedWeight) {
  userHealthWeightPagination.value = userHealthWeightPagination.value.filter(
    (weight) => weight.id !== deletedWeight
  )
  userHealthWeightNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetWeightTarget(weightTarget) {
  emit('setWeightTarget', weightTarget)
}

function handleFilterChange(newFilter) {
  pageNumber.value = 1
  updateHealthWeightPagination()
}

watch(pageNumber, updateHealthWeightPagination, { immediate: false })
watch(weightFilter, handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthWeightPagination()
})
</script>
