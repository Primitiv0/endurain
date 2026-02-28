<template>
  <!-- Modal add/edit fasting -->
  <div
    class="modal fade"
    :id="action == 'add' ? 'addFastingModal' : action == 'edit' ? editFastingId : ''"
    tabindex="-1"
    :aria-labelledby="action == 'add' ? 'addFastingModal' : action == 'edit' ? editFastingId : ''"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="addFastingModal" v-if="action == 'add'">
            {{ $t('healthFastingAddEditModalComponent.addFastingModalTitle') }}
          </h1>
          <h1 class="modal-title fs-5" :id="editFastingId" v-else>
            {{ $t('healthFastingAddEditModalComponent.editFastingModalTitle') }}
          </h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            <!-- fasting type field -->
            <label for="fastingTypeAdd">
              <b>* {{ $t('healthFastingAddEditModalComponent.addFastingTypeLabel') }}</b>
            </label>
            <select
              class="form-select mb-3"
              v-model="newEditFastingType"
              name="fastingTypeAdd"
              required
            >
              <option value="16:8">
                16:8 (16h {{ $t('healthFastingAddEditModalComponent.fast') }}, 8h
                {{ $t('healthFastingAddEditModalComponent.eat') }})
              </option>
              <option value="18:6">
                18:6 (18h {{ $t('healthFastingAddEditModalComponent.fast') }}, 6h
                {{ $t('healthFastingAddEditModalComponent.eat') }})
              </option>
              <option value="20:4">
                20:4 (20h {{ $t('healthFastingAddEditModalComponent.fast') }}, 4h
                {{ $t('healthFastingAddEditModalComponent.eat') }})
              </option>
              <option value="OMAD">OMAD (23:1)</option>
              <option value="24h">
                {{ $t('healthFastingAddEditModalComponent.extended') }} 24h
              </option>
              <option value="36h">
                {{ $t('healthFastingAddEditModalComponent.extended') }} 36h
              </option>
              <option value="48h">
                {{ $t('healthFastingAddEditModalComponent.extended') }} 48h
              </option>
              <option value="72h">
                {{ $t('healthFastingAddEditModalComponent.extended') }} 72h
              </option>
              <option value="custom">{{ $t('healthFastingAddEditModalComponent.custom') }}</option>
            </select>

            <!-- Custom duration (only shown when custom is selected) -->
            <div v-if="newEditFastingType === 'custom'" class="mb-3">
              <label for="customDurationHours">
                <b>* {{ $t('healthFastingAddEditModalComponent.customDurationLabel') }}</b>
              </label>
              <div class="input-group">
                <input
                  class="form-control"
                  type="number"
                  min="1"
                  max="72"
                  name="customDurationHours"
                  v-model="customDurationHours"
                  required
                />
                <span class="input-group-text">{{
                  $t('healthFastingAddEditModalComponent.hours')
                }}</span>
              </div>
            </div>

            <!-- start time field -->
            <label for="fastingStartTimeAdd">
              <b>* {{ $t('healthFastingAddEditModalComponent.addFastingStartTimeLabel') }}</b>
            </label>
            <input
              class="form-control mb-3"
              type="datetime-local"
              name="fastingStartTimeAdd"
              v-model="newEditFastingStartTime"
              required
            />

            <!-- notes field -->
            <label for="fastingNotesAdd">
              <b>{{ $t('healthFastingAddEditModalComponent.addFastingNotesLabel') }}</b>
            </label>
            <textarea
              class="form-control mb-3"
              name="fastingNotesAdd"
              v-model="newEditFastingNotes"
              rows="3"
              maxlength="500"
            ></textarea>

            <p>* {{ $t('generalItems.requiredField') }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('generalItems.buttonClose') }}
            </button>
            <button
              type="submit"
              class="btn btn-success"
              data-bs-dismiss="modal"
              v-if="action == 'add'"
            >
              {{ $t('healthFastingAddEditModalComponent.addFastingModalTitle') }}
            </button>
            <button type="submit" class="btn btn-success" data-bs-dismiss="modal" v-else>
              {{ $t('healthFastingAddEditModalComponent.editFastingModalTitle') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { health_fasting } from '@/services/health_fastingService'

const props = defineProps({
  action: {
    type: String,
    required: true
  },
  userHealthFasting: {
    type: Object,
    required: false
  }
})

const emit = defineEmits(['isLoadingNewFasting', 'createdFasting', 'editedFasting'])

const { t } = useI18n()
const newEditFastingType = ref('16:8')
const customDurationHours = ref(16)
const newEditFastingStartTime = ref(new Date().toISOString().slice(0, 16))
const newEditFastingNotes = ref('')
const editFastingId = ref('')

// Duration mappings in seconds
const fastingDurations = {
  '16:8': 16 * 3600,
  '18:6': 18 * 3600,
  '20:4': 20 * 3600,
  OMAD: 23 * 3600,
  '24h': 24 * 3600,
  '36h': 36 * 3600,
  '48h': 48 * 3600,
  '72h': 72 * 3600
}

const targetDurationSeconds = computed(() => {
  if (newEditFastingType.value === 'custom') {
    return customDurationHours.value * 3600
  }
  return fastingDurations[newEditFastingType.value] || 16 * 3600
})

if (props.userHealthFasting) {
  newEditFastingType.value = props.userHealthFasting.fasting_type || '16:8'
  newEditFastingStartTime.value = props.userHealthFasting.fast_start_time
    ? new Date(props.userHealthFasting.fast_start_time).toISOString().slice(0, 16)
    : new Date().toISOString().slice(0, 16)
  newEditFastingNotes.value = props.userHealthFasting.notes || ''
  editFastingId.value = `editFastingId${props.userHealthFasting.id}`

  // Check if custom duration
  if (props.userHealthFasting.target_duration_seconds) {
    const hours = props.userHealthFasting.target_duration_seconds / 3600
    if (
      !Object.values(fastingDurations).includes(props.userHealthFasting.target_duration_seconds)
    ) {
      newEditFastingType.value = 'custom'
      customDurationHours.value = hours
    }
  }
}

async function submitAddFasting() {
  emit('isLoadingNewFasting', true)
  try {
    const data = {
      fast_start_time: new Date(newEditFastingStartTime.value).toISOString(),
      fasting_type: newEditFastingType.value,
      target_duration_seconds: targetDurationSeconds.value,
      notes: newEditFastingNotes.value || null,
      source: 'manual'
    }

    const createdFasting = await health_fasting.createHealthFasting(data)

    emit('isLoadingNewFasting', false)
    emit('createdFasting', createdFasting)

    push.success(t('healthFastingAddEditModalComponent.successAddFasting'))
  } catch (error) {
    emit('isLoadingNewFasting', false)
    push.error(`${t('healthFastingAddEditModalComponent.errorAddFasting')} - ${error.toString()}`)
  }
}

function submitEditFasting() {
  emit('editedFasting', {
    id: props.userHealthFasting.id,
    user_id: props.userHealthFasting.user_id,
    fast_start_time: new Date(newEditFastingStartTime.value).toISOString(),
    fasting_type: newEditFastingType.value,
    target_duration_seconds: targetDurationSeconds.value,
    notes: newEditFastingNotes.value || null
  })
}

function handleSubmit() {
  if (props.action === 'add') {
    submitAddFasting()
  } else {
    submitEditFasting()
  }
}
</script>
