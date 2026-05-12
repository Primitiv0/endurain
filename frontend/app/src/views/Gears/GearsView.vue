<template>
  <h1>{{ $t('gearsView.title') }}</h1>
  <div class="row row-gap-3">
    <div class="col-lg-3 col-md-12">
      <div class="p-3 bg-body-tertiary rounded shadow-sm">
        <!-- Add gear zone -->
        <span>{{ $t('gearsView.buttonAddGear') }}</span>
        <a
          class="w-100 btn btn-primary mt-2"
          href="#"
          role="button"
          data-bs-toggle="modal"
          data-bs-target="#addGearModal"
        >
          {{ $t('gearsView.buttonAddGear') }}
        </a>

        <!-- Add gear modal -->
        <GearsAddEditUserModalComponent
          :action="'add'"
          @createdGear="addGearList"
          @isLoadingNewGear="setIsLoadingNewGear"
        />

        <!-- Search gear by nickname zone -->
        <p class="mt-2">{{ $t('gearsView.subTitleSearchGearByNickname') }}</p>
        <form>
          <div class="mb-3">
            <input
              class="form-control"
              type="text"
              name="gearNickname"
              :placeholder="$t('gearsView.placeholderSearchGearByNickname')"
              v-model="searchNickname"
              required
            />
          </div>
        </form>
      </div>
    </div>
    <div class="col">
      <div class="p-3 bg-body-tertiary rounded shadow-sm">
        <!-- Iterating over userGears to display them -->
        <div class="placeholder-glow" v-if="isLoading">
          <span class="placeholder col-8 bg-secondary rounded"></span>
        </div>
        <div class="d-flex align-items-center justify-content-between" v-else>
          <span class="mb-1"
            >{{ $t('gearsView.displayUserNumberOfGears1') }}{{ userGearsNumber
            }}{{ $t('gearsView.displayUserNumberOfGears2') }}{{ userGears.length
            }}{{ $t('gearsView.displayUserNumberOfGears3') }}</span
          >
          <FilterDropdownComponent
            :options="filterOptions"
            v-model="filterValues"
            :aria-label="$t('generalItems.filterOptionsLabel')"
          />
        </div>

        <!-- Displaying loading new gear if applicable -->
        <ListWithIconPlaceholderComponent :numberOfRows="1" v-if="isLoadingNewGear" />

        <!-- Displaying loading if gears are updating -->
        <ListWithIconPlaceholderComponent class="mt-2" :numberOfRows="5" v-if="isLoading" />
        <!-- List gears -->
        <div v-else-if="userGears && userGears.length">
          <ul class="list-group list-group-flush" v-for="gear in userGears" :key="gear.id">
            <GearsListComponent
              :gear="gear"
              @editedGear="editGearList"
              @gearDeleted="updateGearListOnDelete"
            />
          </ul>

          <!-- pagination area -->
          <PaginationComponent
            :totalPages="totalPages"
            :pageNumber="pageNumber"
            @pageNumberChanged="setPageNumber"
            v-if="!searchNickname && !isLoading"
          />
        </div>
        <!-- Displaying a message or component when there are no activities -->
        <NoItemsFoundComponent v-else />
      </div>
    </div>
  </div>
  <!-- back button -->
  <BackButtonComponent />
</template>

<script setup>
// Importing the vue composition API
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
// import lodash
import { debounce } from 'lodash'
// Import Notivue push
import { push } from 'notivue'
// Importing the components
import NoItemsFoundComponent from '@/components/GeneralComponents/NoItemsFoundComponents.vue'
import ListWithIconPlaceholderComponent from '@/components/PlaceholderComponents/ListWithIconPlaceholderComponent.vue'
import BackButtonComponent from '@/components/GeneralComponents/BackButtonComponent.vue'
import PaginationComponent from '@/components/GeneralComponents/PaginationComponent.vue'
import GearsAddEditUserModalComponent from '@/components/Gears/GearsAddEditGearModalComponent.vue'
import GearsListComponent from '@/components/Gears/GearsListComponent.vue'
import FilterDropdownComponent from '@/components/GeneralComponents/FilterDropdownComponent.vue'
// Importing the services
import { gears } from '@/services/gearsService'
// Importing the stores
import { useServerSettingsStore } from '@/stores/serverSettingsStore'

const { t } = useI18n()
const serverSettingsStore = useServerSettingsStore()
const route = useRoute()
const isLoading = ref(true)
const isLoadingNewGear = ref(false)
const userGears = ref([])
const userGearsNumber = ref(0)
const pageNumber = ref(1)
const totalPages = ref(1)
const numRecords = serverSettingsStore.serverSettings.num_records_per_page || 25
const searchNickname = ref('')
const filterValues = ref({
  showInactive: false
})
const filterOptions = computed(() => [
  { id: 'showInactive', label: t('gearsView.showInactiveGears') }
])

const performSearch = debounce(async () => {
  // If the search nickname is empty, reset the list to initial state.
  if (!searchNickname.value) {
    // Reset the list to the initial state when search text is cleared
    pageNumber.value = 1
    // Fetch gears
    await updateGears()
    // Exit the function
    return
  }
  try {
    // Fetch the users based on the search nickname.
    isLoading.value = true
    userGears.value = await gears.getGearContainsNickname(searchNickname.value)
  } catch (error) {
    push.error(`${t('gearsView.errorGearNotFound')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}, 500)

function setPageNumber(page) {
  // Set the page number.
  pageNumber.value = page
}

async function updateGears() {
  try {
    // Set the loading variable to true.
    isLoading.value = true

    const gearsDataPagination = await gears.getUserGearsWithPagination(
      pageNumber.value,
      numRecords,
      filterValues.value
    )
    userGears.value = gearsDataPagination.records
    userGearsNumber.value = gearsDataPagination.total
    totalPages.value = Math.ceil(userGearsNumber.value / numRecords)
  } catch (error) {
    // If there is an error, set the error message and show the error alert.
    push.error(`${t('gearsView.errorFetchingGears')} - ${error}`)
  } finally {
    // Set the loading variable to false.
    isLoading.value = false
  }
}

onMounted(async () => {
  if (route.query.gearDeleted === 'true') {
    // Set the gearDeleted value to true and show the success alert.
    push.success(t('gearsView.successGearDeleted'))
  }

  if (route.query.gearFound === 'false') {
    // Set the gearFound value to false and show the error alert.
    push.error(`${t('gearsView.errorGearNotFound')} - ID:${route.query.id}`)
  }

  // Fetch gears
  await updateGears()
})

function addGearList(createdGear) {
  userGears.value.unshift(createdGear)
  userGearsNumber.value++
}

function editGearList(editedGear) {
  const index = userGears.value.findIndex((gear) => gear.id === editedGear.id)
  userGears.value[index] = editedGear
}

function setIsLoadingNewGear(state) {
  isLoadingNewGear.value = state
}

function updateGearListOnDelete(gearDeletedId) {
  userGears.value = userGears.value.filter((gear) => gear.id !== gearDeletedId)
  userGearsNumber.value--
}

// Watch the search nickname variable.
watch(searchNickname, performSearch, { immediate: false })

// Watch the page number variable.
watch(pageNumber, updateGears, { immediate: false })
watch(filterValues, updateGears, { immediate: false })
</script>
