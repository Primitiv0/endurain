<template>
  <li class="list-group-item bg-body-tertiary rounded border-0 mb-1">
    <div class="d-flex justify-content-between align-items-start">
      <div class="flex-grow-1">
        <!-- Name, prefix, status badge -->
        <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
          <span class="fw-bold">{{ apiKey.name }}</span>
          <code class="badge bg-secondary font-monospace">{{ apiKey.key_prefix }}...</code>
          <span
            class="badge"
            :class="
              apiKey.is_active
                ? 'bg-success-subtle border border-success-subtle text-success-emphasis'
                : 'bg-danger-subtle border border-danger-subtle text-danger-emphasis'
            "
          >
            {{
              apiKey.is_active
                ? t('settingsSecurityZone.apiKeyStatusActive')
                : t('settingsSecurityZone.apiKeyStatusRevoked')
            }}
          </span>
        </div>

        <!-- Scope badges -->
        <div class="d-flex flex-wrap gap-1 mb-1">
          <span
            v-for="scope in parsedScopes"
            :key="scope"
            class="badge bg-primary-subtle border border-primary-subtle text-primary-emphasis font-monospace"
          >
            {{ scope }}
          </span>
        </div>

        <!-- Metadata -->
        <small class="text-muted d-flex flex-wrap gap-3">
          <span>
            <b>{{ t('settingsSecurityZone.apiKeyCreatedAtLabel') }}:</b>
            {{ formatDateMed(apiKey.created_at) }}
          </span>
          <span>
            <b>{{ t('settingsSecurityZone.apiKeyLastUsedLabel') }}:</b>
            {{
              apiKey.last_used_at
                ? formatDateMed(apiKey.last_used_at)
                : t('settingsSecurityZone.apiKeyNever')
            }}
          </span>
          <span>
            <b>{{ t('settingsSecurityZone.apiKeyExpiryLabel') }}:</b>
            {{
              apiKey.expires_at
                ? formatDateMed(apiKey.expires_at)
                : t('settingsSecurityZone.apiKeyNever')
            }}
          </span>
        </small>
      </div>

      <!-- Action buttons -->
      <div class="d-flex gap-1 ms-2">
        <!-- Revoke (only when active) -->
        <a
          v-if="apiKey.is_active"
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#revokeApiKeyModal${apiKey.id}`"
          :title="t('settingsSecurityZone.apiKeyRevokeButton')"
        >
          <font-awesome-icon :icon="['fas', 'ban']" />
        </a>

        <!-- Delete -->
        <a
          class="btn btn-link btn-lg link-body-emphasis"
          href="#"
          role="button"
          data-bs-toggle="modal"
          :data-bs-target="`#deleteApiKeyModal${apiKey.id}`"
          :title="t('settingsSecurityZone.apiKeyDeleteButton')"
        >
          <font-awesome-icon :icon="['fas', 'fa-trash-can']" />
        </a>

        <!-- Revoke confirm modal -->
        <ModalComponent
          v-if="apiKey.is_active"
          :modalId="`revokeApiKeyModal${apiKey.id}`"
          :title="t('settingsSecurityZone.apiKeyRevokeConfirmTitle')"
          :body="`${t('settingsSecurityZone.apiKeyRevokeConfirmBody')}<b>${apiKey.name}</b>?`"
          actionButtonType="warning"
          :actionButtonText="t('settingsSecurityZone.apiKeyRevokeButton')"
          @submitAction="submitRevoke"
        />

        <!-- Delete confirm modal -->
        <ModalComponent
          :modalId="`deleteApiKeyModal${apiKey.id}`"
          :title="t('settingsSecurityZone.apiKeyDeleteConfirmTitle')"
          :body="`${t('settingsSecurityZone.apiKeyDeleteConfirmBody')}<b>${apiKey.name}</b>?`"
          actionButtonType="danger"
          :actionButtonText="t('settingsSecurityZone.apiKeyDeleteButton')"
          @submitAction="submitDelete"
        />
      </div>
    </div>
  </li>
</template>

<script>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDateMed } from '@/utils/dateTimeUtils'
import ModalComponent from '@/components/Modals/ModalComponent.vue'

export default {
  components: {
    ModalComponent
  },
  props: {
    apiKey: {
      type: Object,
      required: true
    }
  },
  emits: ['keyRevoked', 'keyDeleted'],
  setup(props, { emit }) {
    const { t } = useI18n()

    /**
     * Parses the JSON-encoded scopes string returned by the API.
     *
     * @returns {string[]} Array of scope strings.
     */
    const parsedScopes = computed(() => {
      try {
        return JSON.parse(props.apiKey.scopes)
      } catch {
        return []
      }
    })

    /**
     * Emits the keyRevoked event with the API key id.
     *
     * @returns void
     */
    function submitRevoke() {
      emit('keyRevoked', props.apiKey.id)
    }

    /**
     * Emits the keyDeleted event with the API key id.
     *
     * @returns void
     */
    function submitDelete() {
      emit('keyDeleted', props.apiKey.id)
    }

    return {
      t,
      formatDateMed,
      parsedScopes,
      submitRevoke,
      submitDelete
    }
  }
}
</script>
