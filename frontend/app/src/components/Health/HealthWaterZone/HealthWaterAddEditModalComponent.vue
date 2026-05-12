<template>
  <!-- Modal add/edit water intake -->
  <div
    class="modal fade"
    :id="action == 'add' ? 'addWaterModal' : action == 'edit' ? editWaterId : ''"
    tabindex="-1"
    :aria-labelledby="action == 'add' ? 'addWaterModal' : action == 'edit' ? editWaterId : ''"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="addWaterModal" v-if="action == 'add'">
            {{ $t('healthWaterAddEditModalComponent.addWaterModalTitle') }}
          </h1>
          <h1 class="modal-title fs-5" :id="editWaterId" v-else>
            {{ $t('healthWaterAddEditModalComponent.editWaterModalTitle') }}
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
            <!-- amount_ml field -->
            <label for="waterAmountAdd">
              <b>* {{ $t('healthWaterAddEditModalComponent.addWaterAmountLabel') }}</b>
            </label>
            <div class="input-group mb-3">
              <input
                class="form-control"
                type="number"
                step="1"
                min="0"
                :max="isImperial ? 676 : 20000"
                name="waterAmountAdd"
                v-model="newEditWaterAmount"
                required
              />
              <span class="input-group-text">{{
                isImperial ? $t('generalItems.unitsFlOz') : $t('generalItems.unitsMl')
              }}</span>
            </div>

            <!-- date field -->
            <label for="waterDateAdd">
              <b>* {{ $t('healthWaterAddEditModalComponent.addWaterDateLabel') }}</b>
            </label>
            <input
              class="form-control"
              type="date"
              name="waterDateAdd"
              v-model="newEditWaterDate"
              required
            />

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
              {{ $t('healthWaterAddEditModalComponent.addWaterModalTitle') }}
            </button>
            <button type="submit" class="btn btn-success" data-bs-dismiss="modal" v-else>
              {{ $t('healthWaterAddEditModalComponent.editWaterModalTitle') }}
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
import { health_water } from '@/services/health_waterService'
import { useAuthStore } from '@/stores/authStore'
import { mlToFlOz, flOzToMl } from '@/utils/unitsUtils'

const props = defineProps({
  action: {
    type: String,
    required: true
  },
  userHealthWater: {
    type: Object,
    required: false
  }
})

const emit = defineEmits(['isLoadingNewWater', 'createdWater', 'editedWater'])

const { t } = useI18n()
const authStore = useAuthStore()
const isImperial = authStore?.user?.units === 'imperial'
const newEditWaterAmount = ref(isImperial ? mlToFlOz(250) : 250)
const newEditWaterDate = ref(new Date().toISOString().split('T')[0])
const editWaterId = ref('')

if (props.userHealthWater) {
  newEditWaterAmount.value = isImperial
    ? mlToFlOz(props.userHealthWater.amount_ml)
    : props.userHealthWater.amount_ml
  newEditWaterDate.value = props.userHealthWater.date
  editWaterId.value = `editWaterId${props.userHealthWater.id}`
}

async function submitAddWater() {
  emit('isLoadingNewWater', true)
  try {
    const data = {
      amount_ml: isImperial
        ? flOzToMl(Number(newEditWaterAmount.value))
        : Number(newEditWaterAmount.value),
      date: newEditWaterDate.value
    }

    const createdWater = await health_water.createHealthWater(data)

    emit('isLoadingNewWater', false)
    emit('createdWater', createdWater)

    push.success(t('healthWaterAddEditModalComponent.successAddWater'))
  } catch (error) {
    emit('isLoadingNewWater', false)
    push.error(`${t('healthWaterAddEditModalComponent.errorAddWater')} - ${error.toString()}`)
  }
}

function submitEditWater() {
  emit('editedWater', {
    id: props.userHealthWater.id,
    user_id: props.userHealthWater.user_id,
    amount_ml: isImperial
      ? flOzToMl(Number(newEditWaterAmount.value))
      : Number(newEditWaterAmount.value),
    date: newEditWaterDate.value
  })
}

function handleSubmit() {
  if (props.action === 'add') {
    submitAddWater()
  } else {
    submitEditWater()
  }
}
</script>
