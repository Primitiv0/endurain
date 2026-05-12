<template>
  <div class="row mt-3" aria-hidden="true">
    <div v-for="n in numberOfCards" :key="n" class="col-md-4 col-sm-6 mb-2">
      <div class="card text-center h-100">
        <div class="card-body">
          <h6 class="card-subtitle mb-2 placeholder-glow">
            <span class="placeholder col-6 bg-secondary rounded"></span>
          </h6>
          <h4 class="card-title placeholder-glow">
            <span class="placeholder col-8 bg-secondary rounded"></span>
          </h4>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  /** Number of stat cards to display. */
  numberOfCards?: number
}>()
</script>
