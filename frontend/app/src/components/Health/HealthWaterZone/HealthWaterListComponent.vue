<template>
  <li class="list-group-item d-flex justify-content-between p-0 bg-body-tertiary">
    <div class="d-flex align-items-center">
      <div>
        <div class="fw-bold">
          <span v-if="isImperial"
            >{{ mlToFlOz(userHealthWater.amount_ml) }} {{ $t('generalItems.unitsFlOz') }}</span
          >
          <span v-else>{{ userHealthWater.amount_ml }} {{ $t('generalItems.unitsMl') }}</span>
        </div>
        <span>
          {{ $t('healthWaterListComponent.labelDate') }}:
          {{ formatDateShort(userHealthWater.date) }}
        </span>
      </div>
    </div>
    <div>
      <!-- edit button -->
      <a
        class="btn btn-link btn-lg link-body-emphasis"
        href="#"
        role="button"
        data-bs-toggle="modal"
        :data-bs-target="`#editWaterId${userHealthWater.id}`"
      >
        <font-awesome-icon :icon="['fas', 'fa-pen-to-square']" />
      </a>

      <HealthWaterAddEditModalComponent
        :action="'edit'"
        :userHealthWater="userHealthWater"
        @editedWater="updateWaterListEdited"
      />

      <!-- delete button -->
      <a
        class="btn btn-link btn-lg link-body-emphasis"
        href="#"
        role="button"
        data-bs-toggle="modal"
        :data-bs-target="`#deleteWaterModal${userHealthWater.id}`"
      >
        <font-awesome-icon :icon="['fas', 'fa-trash-can']" />
      </a>

      <ModalComponent
        :modalId="`deleteWaterModal${userHealthWater.id}`"
        :title="t('healthWaterListComponent.modalDeleteWaterTitle')"
        :body="`${t('healthWaterListComponent.modalDeleteWaterBody')}<b>${userHealthWater.date}</b>?`"
        :actionButtonType="`danger`"
        :actionButtonText="t('healthWaterListComponent.modalDeleteWaterTitle')"
        @submitAction="submitDeleteWater"
      />
    </div>
  </li>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { health_water } from '@/services/health_waterService'
import { useAuthStore } from '@/stores/authStore'
import { mlToFlOz } from '@/utils/unitsUtils'
import HealthWaterAddEditModalComponent from './HealthWaterAddEditModalComponent.vue'
import ModalComponent from '@/components/Modals/ModalComponent.vue'
import { formatDateShort } from '@/utils/dateTimeUtils'

const props = defineProps({
  userHealthWater: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['editedWater', 'deletedWater'])

const { t } = useI18n()
const authStore = useAuthStore()
const isImperial = authStore?.user?.units === 'imperial'

async function updateWaterListEdited(editedWater) {
  try {
    await health_water.editHealthWater(editedWater)
    emit('editedWater', editedWater)
    push.success(t('healthWaterListComponent.successEditWater'))
  } catch (error) {
    push.error(`${t('healthWaterListComponent.errorEditWater')} - ${error.toString()}`)
  }
}

async function submitDeleteWater() {
  try {
    await health_water.deleteHealthWater(props.userHealthWater.id)
    emit('deletedWater', props.userHealthWater.id)
    push.success(t('healthWaterListComponent.successDeleteWater'))
  } catch (error) {
    push.error(`${t('healthWaterListComponent.errorDeleteWater')} - ${error.toString()}`)
  }
}
</script>
