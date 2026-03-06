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
          data-bs-target="#addWaterModal"
          >{{ $t('healthWaterZoneComponent.buttonAddWater') }}</a
        >
        <a
          class="w-100 btn btn-primary shadow-sm ms-1"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addWaterTargetModal"
          >{{ $t('healthWaterZoneComponent.buttonWaterTarget') }}</a
        >
      </div>

      <HealthWaterAddEditModalComponent
        :action="'add'"
        @isLoadingNewWater="updateIsLoadingNewWater"
        @createdWater="updateWaterListAdded"
      />

      <ModalComponentNumberInput
        modalId="addWaterTargetModal"
        :title="t('healthWaterZoneComponent.buttonWaterTarget')"
        :numberFieldLabel="t('healthWaterZoneComponent.modalWaterTargetLabel')"
        actionButtonType="success"
        :actionButtonText="t('generalItems.buttonSubmit')"
        :numberDefaultValue="props.userHealthTargets?.water_ml || parseInt(2000)"
        @numberToEmitAction="submitSetWaterTarget"
      />

      <BarChartPlaceholderComponent
        class="mt-3"
        :number-of-bars="7"
        v-if="isLoadingParent || isLoading"
      />
      <HealthWaterBarChartComponent
        class="mt-3"
        :userHealthTargets="userHealthTargets"
        :userHealthWater="userHealthWaterPagination"
        :isLoading="isLoading"
        v-else-if="userHealthWaterPagination && userHealthWaterPagination.length"
      />

      <div class="row row-gap-3 mt-3 align-items-center">
        <div class="col-sm-7">
          <div class="placeholder-glow" v-if="isLoadingParent || isLoading">
            <span class="placeholder col-8 bg-secondary rounded"></span>
          </div>
          <span v-else>
            {{ $t('healthWaterZoneComponent.labelNumberOfHealthWater1') }}{{ userHealthWaterNumber
            }}{{ $t('healthWaterZoneComponent.labelNumberOfHealthWater2')
            }}{{ userHealthWaterPagination.length
            }}{{ $t('healthWaterZoneComponent.labelNumberOfHealthWater3') }}
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

      <ListPlaceholderComponent class="mt-3" :numberOfRows="1" v-if="isLoadingNewWater" />

      <ListPlaceholderComponent
        class="mt-3"
        :numberOfRows="5"
        v-if="isLoadingParent || isLoading"
      />
      <div v-else-if="userHealthWaterPagination && userHealthWaterPagination.length" class="mt-3">
        <ul
          class="my-3 list-group list-group-flush"
          v-for="waterRecord in userHealthWaterPagination"
          :key="waterRecord.id"
        >
          <HealthWaterListComponent
            :userHealthWater="waterRecord"
            @deletedWater="updateWaterListDeleted"
            @editedWater="updateWaterListEdited"
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
import HealthWaterAddEditModalComponent from './HealthWaterZone/HealthWaterAddEditModalComponent.vue'
import HealthWaterBarChartComponent from './HealthWaterZone/HealthWaterBarChartComponent.vue'
import HealthWaterListComponent from './HealthWaterZone/HealthWaterListComponent.vue'
import BarChartPlaceholderComponent from '../PlaceholderComponents/BarChartPlaceholderComponent.vue'
import NoItemsFoundComponent from '../GeneralComponents/NoItemsFoundComponents.vue'
import PaginationComponent from '../GeneralComponents/PaginationComponent.vue'
import ModalComponentNumberInput from '../Modals/ModalComponentNumberInput.vue'
import ListPlaceholderComponent from '../PlaceholderComponents/ListPlaceholderComponent.vue'
import { health_water } from '@/services/health_waterService'
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

const emit = defineEmits(['setWaterTarget'])

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const isLoadingNewWater = ref(false)
const isLoading = ref(false)
const userHealthWaterNumber = ref(0)
const userHealthWaterPagination = ref([])
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

async function updateHealthWaterPagination() {
  try {
    isLoading.value = true
    const waterDataPagination = await health_water.getUserHealthWaterWithPagination(
      pageNumber.value,
      numRecords.value,
      paginationFilter.value,
      intervalFilter.value
    )
    userHealthWaterPagination.value = waterDataPagination.records
    userHealthWaterNumber.value = waterDataPagination.total
    totalPages.value = Math.ceil(userHealthWaterNumber.value / numRecords.value)
  } catch (error) {
    push.error(`${t('healthWaterZoneComponent.errorFetchingHealthWater')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

function updateIsLoadingNewWater(value) {
  isLoadingNewWater.value = value
}

function updateWaterListAdded(createdWater) {
  isLoadingNewWater.value = true
  if (userHealthWaterPagination.value) {
    const index = userHealthWaterPagination.value.findIndex((item) => item.id === createdWater.id)
    if (index !== -1) {
      userHealthWaterPagination.value[index] = createdWater
    } else {
      userHealthWaterPagination.value.unshift(createdWater)
      userHealthWaterNumber.value++
    }
  } else {
    userHealthWaterPagination.value = [createdWater]
  }
  isLoadingNewWater.value = false
}

function updateWaterListEdited(editedWater) {
  const index = userHealthWaterPagination.value.findIndex((w) => w.id === editedWater.id)
  if (index !== -1) {
    userHealthWaterPagination.value[index] = editedWater
  }
}

function updateWaterListDeleted(deletedWaterId) {
  userHealthWaterPagination.value = userHealthWaterPagination.value.filter(
    (w) => w.id !== deletedWaterId
  )
  userHealthWaterNumber.value--
}

function setPageNumber(page) {
  pageNumber.value = page
}

function submitSetWaterTarget(waterTarget) {
  emit('setWaterTarget', waterTarget)
}

function handleFilterChange() {
  pageNumber.value = 1
  updateHealthWaterPagination()
}

watch(pageNumber, updateHealthWaterPagination, { immediate: false })
watch([intervalFilter, paginationFilter], handleFilterChange, { immediate: false })

onMounted(async () => {
  await updateHealthWaterPagination()
})
</script>
