<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <!-- action buttons -->
      <div class="d-flex">
        <a
          class="w-100 btn btn-primary shadow-sm me-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addPoopModal"
          >{{ $t('healthPoopZoneComponent.buttonAddPoop') }}</a
        >
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addPoopTargetModal"
          >{{ $t('healthPoopZoneComponent.buttonPoopTarget') }}</a
        >
      </div>

      <HealthPoopAddEditModalComponent
        :action="'add'"
        @isLoadingNewPoop="updateIsLoadingNewPoop"
        @createdPoop="updatePoopListAdded"
      />

      <ModalComponentNumberInput
        modalId="addPoopTargetModal"
        :title="t('healthPoopZoneComponent.buttonPoopTarget')"
        :numberFieldLabel="t('healthPoopZoneComponent.modalPoopTargetLabel')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :numberDefaultValue="props.userHealthTargets?.poop_count || parseInt(1)"
        @numberToEmitAction="submitSetPoopTarget"
      />

      <BarChartPlaceholderComponent
        class="mt-3"
        :number-of-bars="7"
        v-if="isLoadingParent || isLoading"
      />
      <HealthPoopBarChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthPoop="userHealthPoopPagination"
        :isLoading="isLoading"
        v-else-if="userHealthPoopPagination && userHealthPoopPagination.length"
      />

      <div class="row row-gap-3 mt-3 align-items-center">
        <div class="col-sm-7">
          <div class="placeholder-glow" v-if="isLoadingParent || isLoading">
            <span class="placeholder col-8 bg-secondary rounded"></span>
          </div>
          <span v-else>
            {{ $t('healthPoopZoneComponent.labelNumberOfHealthPoop1') }}{{ userHealthPoopNumber
            }}{{ $t('healthPoopZoneComponent.labelNumberOfHealthPoop2')
            }}{{ userHealthPoopPagination.length
            }}{{ $t('healthPoopZoneComponent.labelNumberOfHealthPoop3') }}
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

      <ListPlaceholderComponent class="mt-3" :numberOfRows="1" v-if="isLoadingNewPoop" />

      <ListPlaceholderComponent
        class="mt-3"
        :numberOfRows="5"
        v-if="isLoadingParent || isLoading"
      />
      <div v-else-if="userHealthPoopPagination && userHealthPoopPagination.length" class="mt-3">
        <ul
          class="my-3 list-group list-group-flush"
          v-for="poopRecord in userHealthPoopPagination"
          :key="poopRecord.id"
        >
          <HealthPoopListComponent
            :userHealthPoop="poopRecord"
            @deletedPoop="updatePoopListDeleted"
            @editedPoop="updatePoopListEdited"
          />
        </ul>

        <PaginationComponent
          :totalPages="totalPages"
          :pageNumber="pageNumber"
          @pageNumberChanged="setPageNumber"
          v-if="paginationFilter !== 'disabled'"
        />
      </div>
      <NoItemsFoundComponent class="mt-3" :show-shadow="false" v-else />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import HealthPoopAddEditModalComponent from './HealthPoopZone/HealthPoopAddEditModalComponent.vue'
import HealthPoopBarChartComponent from './HealthPoopZone/HealthPoopBarChartComponent.vue'
import HealthPoopListComponent from './HealthPoopZone/HealthPoopListComponent.vue'
import BarChartPlaceholderComponent from '../PlaceholderComponents/BarChartPlaceholderComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
import ModalComponentNumberInput from '../Modals/ModalComponentNumberInput.vue'
import ListPlaceholderComponent from '../PlaceholderComponents/ListPlaceholderComponent.vue'
import { health_poop } from '@/services/health_poopService'
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

const emit = defineEmits(['setPoopTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewPoop = ref(false)
const isLoading = ref(false)
const userHealthPoopNumber = ref(0)
const userHealthPoopPagination = ref([])
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

async function updateHealthPoopPagination() {
  try {
    isLoading.value = true
    const poopDataPagination = await health_poop.getUserHealthPoopWithPagination(
      pageNumber.value,
      numRecords.value,
      paginationFilter.value,
      intervalFilter.value
    )
    userHealthPoopPagination.value = poopDataPagination.records
    userHealthPoopNumber.value = poopDataPagination.total
    totalPages.value = Math.ceil(userHealthPoopNumber.value / numRecords.value)
  } catch (error) {
    push.error(`${t('healthPoopZoneComponent.errorFetchingHealthPoop')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function updateIsLoadingNewPoop(value) {
  isLoadingNewPoop.value = value
}

function updatePoopListAdded(createdPoop) {
  isLoadingNewPoop.value = true
  if (userHealthPoopPagination.value) {
    userHealthPoopPagination.value.unshift(createdPoop)
    userHealthPoopNumber.value++
  } else {
    userHealthPoopPagination.value = [createdPoop]
  }
  isLoadingNewPoop.value = false
}

function updatePoopListEdited(editedPoop) {
  const index = userHealthPoopPagination.value.findIndex((p) => p.id === editedPoop.id)
  if (index !== -1) {
    userHealthPoopPagination.value[index] = editedPoop
  }
}

function updatePoopListDeleted(deletedPoopId) {
  userHealthPoopPagination.value = userHealthPoopPagination.value.filter(
    (p) => p.id !== deletedPoopId
  )
  userHealthPoopNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetPoopTarget(poopTarget) {
  emit('setPoopTarget', poopTarget)
}

function handleFilterChange() {
  pageNumber.value = 1
  updateHealthPoopPagination()
}

watch(pageNumber, updateHealthPoopPagination, { immediate: false })
watch([intervalFilter, paginationFilter], handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthPoopPagination()
})
</script>
