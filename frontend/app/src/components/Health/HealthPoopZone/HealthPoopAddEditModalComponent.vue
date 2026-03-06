<template>
  <!-- Modal add/edit poop record -->
  <div
    class="modal fade"
    :id="action == 'add' ? 'addPoopModal' : action == 'edit' ? editPoopId : ''"
    tabindex="-1"
    :aria-labelledby="action == 'add' ? 'addPoopModal' : action == 'edit' ? editPoopId : ''"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="addPoopModal" v-if="action == 'add'">
            {{ $t('healthPoopAddEditModalComponent.addPoopModalTitle') }}
          </h1>
          <h1 class="modal-title fs-5" :id="editPoopId" v-else>
            {{ $t('healthPoopAddEditModalComponent.editPoopModalTitle') }}
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
            <!-- date_time field -->
            <label for="poopDateTimeAdd">
              <b>* {{ $t('healthPoopAddEditModalComponent.addPoopDateTimeLabel') }}</b>
            </label>
            <input
              class="form-control mb-3"
              type="datetime-local"
              name="poopDateTimeAdd"
              v-model="newEditPoopDateTime"
              required
            />

            <!-- bristol_type select -->
            <label for="poopBristolTypeAdd">
              <b>{{ $t('healthPoopAddEditModalComponent.addPoopBristolTypeLabel') }}</b>
            </label>
            <select
              class="form-select mb-3"
              name="poopBristolTypeAdd"
              v-model="newEditPoopBristolType"
            >
              <option :value="null">
                {{ $t('healthPoopAddEditModalComponent.bristolTypeNone') }}
              </option>
              <option v-for="n in 7" :key="n" :value="n">
                {{ $t(`healthPoopAddEditModalComponent.bristolType${n}`) }}
              </option>
            </select>

            <!-- color select -->
            <label for="poopColorAdd">
              <b>{{ $t('healthPoopAddEditModalComponent.addPoopColorLabel') }}</b>
            </label>
            <select class="form-select mb-3" name="poopColorAdd" v-model="newEditPoopColor">
              <option :value="null">
                {{ $t('healthPoopAddEditModalComponent.colorNone') }}
              </option>
              <option v-for="color in poopColors" :key="color" :value="color">
                {{ $t(`healthPoopAddEditModalComponent.color_${color}`) }}
              </option>
            </select>

            <!-- notes field -->
            <label for="poopNotesAdd">
              <b>{{ $t('healthPoopAddEditModalComponent.addPoopNotesLabel') }}</b>
            </label>
            <textarea
              class="form-control"
              name="poopNotesAdd"
              v-model="newEditPoopNotes"
              rows="3"
              maxlength="500"
            ></textarea>

            <p class="mt-2">* {{ $t('generalItems.requiredField') }}</p>
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
              {{ $t('healthPoopAddEditModalComponent.addPoopModalTitle') }}
            </button>
            <button type="submit" class="btn btn-success" data-bs-dismiss="modal" v-else>
              {{ $t('healthPoopAddEditModalComponent.editPoopModalTitle') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { health_poop } from '@/services/health_poopService'

const props = defineProps({
  action: {
    type: String,
    required: true
  },
  userHealthPoop: {
    type: Object,
    required: false
  }
})

const emit = defineEmits(['isLoadingNewPoop', 'createdPoop', 'editedPoop'])

const { t } = useI18n()

const poopColors = [
  'brown',
  'dark_brown',
  'light_brown',
  'yellow',
  'green',
  'black',
  'red',
  'white'
]

function nowLocalDateTimeString() {
  const now = new Date()
  now.setSeconds(0, 0)
  return now.toISOString().slice(0, 16)
}

const newEditPoopDateTime = ref(nowLocalDateTimeString())
const newEditPoopBristolType = ref(null)
const newEditPoopColor = ref(null)
const newEditPoopNotes = ref('')
const editPoopId = ref('')

if (props.userHealthPoop) {
  const dt = new Date(props.userHealthPoop.date_time)
  dt.setSeconds(0, 0)
  newEditPoopDateTime.value = dt.toISOString().slice(0, 16)
  newEditPoopBristolType.value = props.userHealthPoop.bristol_type ?? null
  newEditPoopColor.value = props.userHealthPoop.color ?? null
  newEditPoopNotes.value = props.userHealthPoop.notes ?? ''
  editPoopId.value = `editPoopId${props.userHealthPoop.id}`
}

async function submitAddPoop() {
  emit('isLoadingNewPoop', true)
  try {
    const data = {
      date_time: newEditPoopDateTime.value,
      bristol_type: newEditPoopBristolType.value,
      color: newEditPoopColor.value,
      notes: newEditPoopNotes.value || null
    }

    const createdPoop = await health_poop.createHealthPoop(data)

    emit('isLoadingNewPoop', false)
    emit('createdPoop', createdPoop)

    push.success(t('healthPoopAddEditModalComponent.successAddPoop'))
  } catch (error) {
    emit('isLoadingNewPoop', false)
    push.error(`${t('healthPoopAddEditModalComponent.errorAddPoop')} - ${error.toString()}`)
  }
}

function submitEditPoop() {
  emit('editedPoop', {
    id: props.userHealthPoop.id,
    user_id: props.userHealthPoop.user_id,
    date_time: newEditPoopDateTime.value,
    bristol_type: newEditPoopBristolType.value,
    color: newEditPoopColor.value,
    notes: newEditPoopNotes.value || null
  })
}

function handleSubmit() {
  if (props.action === 'add') {
    submitAddPoop()
  } else {
    submitEditPoop()
  }
}
</script>
