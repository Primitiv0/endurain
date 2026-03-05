<template>
  <div class="col-lg-4 col-md-12">
    <CardPlaceholderComponent v-if="isLoading" />
    <div class="card mb-3 text-center shadow-sm" v-else>
      <div class="card-header">
        <h4>{{ title }}</h4>
      </div>
      <div class="card-body">
        <h1>{{ value ?? noDataLabel }}</h1>
        <span v-if="subtitle" class="text-muted">{{ subtitle }}</span>
      </div>
      <div class="card-footer text-body-secondary">
        <!-- Target mode: card has a target concept (noTargetLabel is provided) -->
        <template v-if="noTargetLabel">
          <template v-if="targetDisplayValue">
            <font-awesome-icon
              :icon="['fas', 'angle-down']"
              class="me-1"
              v-if="arrowDirection === 'down'"
            />
            <font-awesome-icon
              :icon="['fas', 'angle-up']"
              class="me-1"
              v-else-if="arrowDirection === 'up'"
            />
            <span>{{ targetDisplayValue }}</span>
          </template>
          <span v-else>{{ noTargetLabel }}</span>
        </template>
        <!-- Text mode: simple footer text -->
        <span v-else>{{ footerText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CardPlaceholderComponent from '../../PlaceholderComponents/CardPlaceholderComponent.vue'

/**
 * Reusable health dashboard card with loading placeholder and prop-driven body/footer.
 *
 * Supports two footer modes:
 * - **Target mode**: when `noTargetLabel` is provided. Shows arrow + `targetDisplayValue`,
 *   or falls back to `noTargetLabel` when no target is set.
 * - **Text mode**: when `noTargetLabel` is not provided. Shows `footerText`.
 */
defineProps<{
  /** Card header title text. */
  title: string
  /** Whether to show the loading placeholder. */
  isLoading: boolean
  /** Pre-formatted display value for the card body, or null to show noDataLabel. */
  value: string | null
  /** Fallback text shown when value is null. */
  noDataLabel: string
  /** Optional subtitle shown below the main value (e.g., fasting type). */
  subtitle?: string | null
  /** Pre-formatted target display value (e.g., "8h 00m"). Activates target footer mode. */
  targetDisplayValue?: string | null
  /** Text shown when no target is set. Presence of this prop enables target footer mode. */
  noTargetLabel?: string
  /** Arrow direction for target comparison: 'up', 'down', or null for no arrow. */
  arrowDirection?: 'up' | 'down' | null
  /** Simple footer text for non-target cards (text footer mode). */
  footerText?: string
}>()
</script>
