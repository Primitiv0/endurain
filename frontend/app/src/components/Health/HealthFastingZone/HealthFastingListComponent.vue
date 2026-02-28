<template>
  <li
    class="list-group-item p-0 bg-body-tertiary"
    :class="{ 'shadow rounded p-3': fastingDetails }"
  >
    <div class="d-flex justify-content-between align-items-center">
      <div class="d-flex align-items-center">
        <div>
          <div class="fw-bold">
            <span>{{ userHealthFasting.fasting_type }}</span>
            <span class="ms-2" v-if="userHealthFasting.actual_duration_seconds">
              ({{ formatSecondsToHoursMinutesSeconds(userHealthFasting.actual_duration_seconds) }})
            </span>
          </div>
          <span class="text-muted">
            {{ formatTime(userHealthFasting.fast_start_time) }}
            <span v-if="userHealthFasting.fast_end_time">
              → {{ formatTime(userHealthFasting.fast_end_time) }}
            </span>
          </span>
        </div>
      </div>
      <div>
        <span class="badge me-2" :class="getStatusBadgeClass">
          {{ getStatusLabel }}
        </span>
        <span
          class="align-middle me-3 d-none d-sm-inline"
          v-if="userHealthFasting.source === 'garmin'"
        >
          <img :src="INTEGRATION_LOGOS.garminConnectApp" alt="Garmin Connect logo" height="22" />
        </span>

        <!-- button toggle fasting details -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          data-bs-toggle="collapse"
          :href="`#collapseFastingDetails${userHealthFasting.id}`"
          role="button"
          aria-expanded="false"
          :aria-controls="`collapseFastingDetails${userHealthFasting.id}`"
          v-if="userHealthFasting.notes"
        >
          <font-awesome-icon :icon="['fas', 'caret-down']" v-if="!fastingDetails" />
          <font-awesome-icon :icon="['fas', 'caret-up']" v-else />
        </a>
        <!-- edit fasting button -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#editFastingId${userHealthFasting.id}`"
        >
          <font-awesome-icon :icon="['fas', 'fa-pen-to-square']" />
        </a>

        <HealthFastingAddEditModalComponent
          :action="'edit'"
          :userHealthFasting="userHealthFasting"
          @editedFasting="updateFastingListEdited"
        />

        <!-- delete fasting button -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#deleteFastingModal${userHealthFasting.id}`"
        >
          <font-awesome-icon :icon="['fas', 'fa-trash-can']" />
        </a>

        <ModalComponent
          :modalId="`deleteFastingModal${userHealthFasting.id}`"
          :title="t('healthFastingListComponent.modalDeleteFastingTitle')"
          :body="`${t('healthFastingListComponent.modalDeleteFastingBody')}<b>${formatTime(userHealthFasting.fast_start_time)}</b>?`"
          :actionButtonType="`danger`"
          :actionButtonText="t('healthFastingListComponent.modalDeleteFastingTitle')"
          @submitAction="submitDeleteFasting"
        />
      </div>
    </div>
    <div
      class="collapse"
      :id="`collapseFastingDetails${userHealthFasting.id}`"
      v-if="userHealthFasting.notes"
    >
      <span
        ><strong>{{ $t('healthFastingListComponent.notesLabel') }}</strong>
        {{ userHealthFasting.notes }}</span
      >
    </div>
  </li>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { health_fasting } from '@/services/health_fastingService'
import HealthFastingAddEditModalComponent from './HealthFastingAddEditModalComponent.vue'
import ModalComponent from '@/components/Modals/ModalComponent.vue'
import { INTEGRATION_LOGOS } from '@/constants/integrationLogoConstants'
import { formatTime, formatSecondsToHoursMinutesSeconds } from '@/utils/dateTimeUtils'

const props = defineProps({
  userHealthFasting: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['editedFasting', 'deletedFasting'])

const { t } = useI18n()
const fastingDetails = ref(false)

const getStatusBadgeClass = computed(() => {
  switch (props.userHealthFasting.status) {
    case 'completed':
      return 'bg-success'
    case 'in_progress':
      return 'bg-primary'
    case 'broken':
      return 'bg-warning text-dark'
    case 'cancelled':
      return 'bg-secondary'
    default:
      return 'bg-secondary'
  }
})

const getStatusLabel = computed(() => {
  switch (props.userHealthFasting.status) {
    case 'completed':
      return t('healthFastingListComponent.statusCompleted')
    case 'in_progress':
      return t('healthFastingListComponent.statusInProgress')
    case 'broken':
      return t('healthFastingListComponent.statusBroken')
    case 'cancelled':
      return t('healthFastingListComponent.statusCancelled')
    default:
      return props.userHealthFasting.status
  }
})

async function updateFastingListEdited(editedFasting) {
  try {
    await health_fasting.editHealthFasting(editedFasting)

    emit('editedFasting', editedFasting)

    push.success(t('healthFastingListComponent.successEditFasting'))
  } catch (error) {
    push.error(`${t('healthFastingListComponent.errorEditFasting')} - ${error.toString()}`)
  }
}

async function submitDeleteFasting() {
  try {
    await health_fasting.deleteHealthFasting(props.userHealthFasting.id)

    emit('deletedFasting', props.userHealthFasting.id)

    push.success(t('healthFastingListComponent.successDeleteFasting'))
  } catch (error) {
    push.error(`${t('healthFastingListComponent.errorDeleteFasting')} - ${error.toString()}`)
  }
}

onMounted(async () => {
  // Attach Bootstrap collapse event listeners to sync icon state
  const collapseElement = document.getElementById(
    `collapseFastingDetails${props.userHealthFasting.id}`
  )
  if (collapseElement) {
    collapseElement.addEventListener('show.bs.collapse', () => {
      fastingDetails.value = true
    })
    collapseElement.addEventListener('hide.bs.collapse', () => {
      fastingDetails.value = false
    })
  }
})
</script>
