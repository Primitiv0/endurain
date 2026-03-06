<template>
  <li class="list-group-item p-0 bg-body-tertiary" :class="{ 'shadow rounded p-3': notesExpanded }">
    <div class="d-flex justify-content-between align-items-center">
      <div class="d-flex align-items-center">
        <div>
          <div class="fw-bold d-flex align-items-center gap-2">
            <span>{{ formatTime(userHealthPoop.date_time) }}</span>
            <span v-if="userHealthPoop.bristol_type" class="badge bg-secondary">
              {{ $t('healthPoopListComponent.labelBristolType') }}
              {{ userHealthPoop.bristol_type }}
            </span>
            <span
              v-if="userHealthPoop.color"
              class="badge"
              :style="colorBadgeStyle(userHealthPoop.color)"
            >
              {{ $t(`healthPoopAddEditModalComponent.color_${userHealthPoop.color}`) }}
            </span>
          </div>
          <span>
            {{ $t('healthPoopListComponent.labelDate') }}:
            {{ formatDateShort(userHealthPoop.date_time) }}
          </span>
        </div>
      </div>
      <div class="d-flex align-items-center">
        <!-- button toggle notes -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          data-bs-toggle="collapse"
          :href="`#poopNotes${userHealthPoop.id}`"
          role="button"
          aria-expanded="false"
          :aria-controls="`poopNotes${userHealthPoop.id}`"
          v-if="userHealthPoop.notes"
        >
          <font-awesome-icon :icon="['fas', 'caret-down']" v-if="!notesExpanded" />
          <font-awesome-icon :icon="['fas', 'caret-up']" v-else />
        </a>

        <!-- edit button -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#editPoopId${userHealthPoop.id}`"
        >
          <font-awesome-icon :icon="['fas', 'fa-pen-to-square']" />
        </a>

        <HealthPoopAddEditModalComponent
          :action="'edit'"
          :userHealthPoop="userHealthPoop"
          @editedPoop="updatePoopListEdited"
        />

        <!-- delete button -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#deletePoopModal${userHealthPoop.id}`"
        >
          <font-awesome-icon :icon="['fas', 'fa-trash-can']" />
        </a>

        <ModalComponent
          :modalId="`deletePoopModal${userHealthPoop.id}`"
          :title="t('healthPoopListComponent.modalDeletePoopTitle')"
          :body="`${t('healthPoopListComponent.modalDeletePoopBody')}<b>${formatTime(userHealthPoop.date_time)} ${formatDateShort(userHealthPoop.date_time)}</b>?`"
          :actionButtonType="`danger`"
          :actionButtonText="t('healthPoopListComponent.modalDeletePoopTitle')"
          @submitAction="submitDeletePoop"
        />
      </div>
    </div>
    <div class="collapse" :id="`poopNotes${userHealthPoop.id}`" v-if="userHealthPoop.notes">
      <p class="mt-3">
        <span class="fw-semibold"> {{ $t('healthPoopListComponent.labelNotes') }}: </span>
        <span>{{ userHealthPoop.notes }}</span>
      </p>
    </div>
  </li>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { health_poop } from '@/services/health_poopService'
import HealthPoopAddEditModalComponent from './HealthPoopAddEditModalComponent.vue'
import ModalComponent from '@/components/Modals/ModalComponent.vue'
import { formatDateShort, formatTime } from '@/utils/dateTimeUtils'

const props = defineProps({
  userHealthPoop: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['editedPoop', 'deletedPoop'])

const { t } = useI18n()
const notesExpanded = ref(false)

const colorMap = {
  brown: '#8B4513',
  dark_brown: '#5C3317',
  light_brown: '#C8956C',
  yellow: '#F5C518',
  green: '#4CAF50',
  black: '#222222',
  red: '#D32F2F',
  white: '#E0E0E0'
}

function colorBadgeStyle(color) {
  const bg = colorMap[color] ?? '#6c757d'
  const isLight = ['yellow', 'white', 'light_brown'].includes(color)
  return {
    backgroundColor: bg,
    color: isLight ? '#333' : '#fff'
  }
}

async function updatePoopListEdited(editedPoop) {
  try {
    await health_poop.editHealthPoop(editedPoop)
    emit('editedPoop', editedPoop)
    push.success(t('healthPoopListComponent.successEditPoop'))
  } catch (error) {
    push.error(`${t('healthPoopListComponent.errorEditPoop')} - ${error.toString()}`)
  }
}

async function submitDeletePoop() {
  try {
    await health_poop.deleteHealthPoop(props.userHealthPoop.id)
    emit('deletedPoop', props.userHealthPoop.id)
    push.success(t('healthPoopListComponent.successDeletePoop'))
  } catch (error) {
    push.error(`${t('healthPoopListComponent.errorDeletePoop')} - ${error.toString()}`)
  }
}

onMounted(() => {
  const collapseElement = document.getElementById(`poopNotes${props.userHealthPoop.id}`)
  if (collapseElement) {
    collapseElement.addEventListener('show.bs.collapse', () => {
      notesExpanded.value = true
    })
    collapseElement.addEventListener('hide.bs.collapse', () => {
      notesExpanded.value = false
    })
  }
})
</script>
