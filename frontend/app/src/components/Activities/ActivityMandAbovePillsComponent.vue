<template>
  <ul class="nav nav-pills mb-3 mt-3 justify-content-center" id="pills-tab" role="tablist">
    <li class="nav-item" role="presentation" v-if="graphItems && graphItems.length > 0">
      <button
        class="nav-link link-body-emphasis"
        :class="{ active: graphItems || graphItems.length > 0 }"
        id="pills-graphs-tab"
        data-bs-toggle="pill"
        data-bs-target="#pills-graphs"
        type="button"
        role="tab"
        aria-controls="pills-graphs"
        :aria-selected="graphItems && graphItems.length > 0 ? true : false"
      >
        {{ $t('activityMandAbovePillsComponent.labelPillGraphs') }}
      </button>
    </li>
    <li
      class="nav-item"
      role="presentation"
      v-if="activityActivityLaps && activityActivityLaps.length > 0"
    >
      <button
        class="nav-link link-body-emphasis"
        :class="{ active: !graphItems || graphItems.length === 0 }"
        id="pills-laps-tab"
        data-bs-toggle="pill"
        data-bs-target="#pills-laps"
        type="button"
        role="tab"
        aria-controls="pills-laps"
        :aria-selected="!graphItems || graphItems.length === 0 ? 'true' : 'false'"
      >
        {{ $t('activityMandAbovePillsComponent.labelPillLaps') }}
      </button>
    </li>
    <li
      class="nav-item"
      role="presentation"
      v-if="activityActivityWorkoutSteps && activityActivityWorkoutSteps.length > 0"
    >
      <button
        class="nav-link link-body-emphasis"
        id="pills-workout-steps-tab"
        data-bs-toggle="pill"
        data-bs-target="#pills-workout-steps"
        type="button"
        role="tab"
        aria-controls="pills-workout-steps"
        aria-selected="false"
      >
        {{ $t('activityMandAbovePillsComponent.labelPillWorkoutSets') }}
      </button>
    </li>
  </ul>

  <div class="tab-content" id="pills-tabContent">
    <div
      class="tab-pane fade show"
      :class="{ active: graphItems || graphItems.length > 0 }"
      id="pills-graphs"
      role="tabpanel"
      aria-labelledby="pills-graphs-tab"
      tabindex="0"
      v-if="graphItems && graphItems.length > 0"
    >
      <div class="row">
        <div class="col-md-2">
          <p>{{ $t('activityMandAbovePillsComponent.labelGraph') }}</p>
          <ul class="nav nav-pills flex-column mb-auto" id="sidebarLineGraph">
            <li class="nav-item" v-for="item in graphItems" :key="item.type">
              <a
                href="javascript:void(0);"
                class="nav-link text-secondary"
                :class="{ 'active text-white': graphSelection === item.type }"
                @click="selectGraph(item.type)"
              >
                {{ item.label }}
              </a>
            </li>
          </ul>
        </div>
        <div class="col">
          <div if="activity">
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'hr' && hrPresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'power' && powerPresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'cad' && cadPresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'ele' && elePresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'vel' && velPresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'pace' && pacePresent"
            />
            <ActivityStreamsLineChartComponent
              :activity="activity"
              :graphSelection="graphSelection"
              :activityStreams="activityActivityStreams"
              v-if="graphSelection === 'temp' && tempPresent"
            />
            <BarChartComponent
              v-if="
                hrZones &&
                Object.keys(hrZones).length > 0 &&
                graphSelection === 'hrZones' &&
                hrPresent
              "
              :labels="hrChartData.labels"
              :values="hrChartData.values"
              :barColors="hrChartData.barColors"
              :timeSeconds="hrChartData.timeSeconds"
              :datalabelsFormatter="
                (value, context) =>
                  formatHrZoneLabel(value, hrChartData.timeSeconds[context.dataIndex])
              "
              :title="$t('activityMandAbovePillsComponent.labelHRZones')"
            />
          </div>

          <!-- Selected graph summary stats (same data shown on small screens) -->
          <div class="mt-3" v-if="graphSelection === 'pace' && pacePresent">
            <div class="d-flex justify-content-between" v-if="formattedPace">
              <span>{{ $t('activityBellowMPillsComponent.labelAvgPace') }}</span>
              <span>
                <b>{{ formattedPace }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.total_elapsed_time">
              <span>{{ $t('activityBellowMPillsComponent.labelElapsedTime') }}</span>
              <span>
                <b>{{ formatSecondsToHoursMinutesSeconds(activity.total_elapsed_time) }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.total_timer_time">
              <span>{{ $t('activityBellowMPillsComponent.labelMovingTime') }}</span>
              <span>
                <b>{{ formatSecondsToHoursMinutesSeconds(activity.total_timer_time) }}</b>
              </span>
            </div>
          </div>

          <div class="mt-3" v-if="graphSelection === 'vel' && velPresent">
            <div class="d-flex justify-content-between" v-if="activity.average_speed">
              <span>{{ $t('activityBellowMPillsComponent.labelAvgSpeed') }}</span>
              <span>
                <b>{{ formatSpeed(t, activity.average_speed, activity, units) }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.max_speed">
              <span>{{ $t('activityBellowMPillsComponent.labelMaxSpeed') }}</span>
              <span>
                <b>{{ formatSpeed(t, activity.max_speed, activity, units) }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.total_elapsed_time">
              <span>{{ $t('activityBellowMPillsComponent.labelElapsedTime') }}</span>
              <span>
                <b>{{ formatSecondsToHoursMinutesSeconds(activity.total_elapsed_time) }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.total_timer_time">
              <span>{{ $t('activityBellowMPillsComponent.labelMovingTime') }}</span>
              <span>
                <b>{{ formatSecondsToHoursMinutesSeconds(activity.total_timer_time) }}</b>
              </span>
            </div>
          </div>

          <div class="mt-3" v-if="graphSelection === 'hr' && hrPresent">
            <div class="d-flex justify-content-between" v-if="activity.average_hr">
              <span>{{ $t('activityBellowMPillsComponent.labelAvgHeartRate') }}</span>
              <span>
                <b>{{ activity.average_hr }}{{ ' ' + $t('generalItems.unitsBpm') }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.max_hr">
              <span>{{ $t('activityBellowMPillsComponent.labelMaxHeartRate') }}</span>
              <span>
                <b>{{ activity.max_hr }}{{ ' ' + $t('generalItems.unitsBpm') }}</b>
              </span>
            </div>
          </div>

          <div class="mt-3" v-if="graphSelection === 'power' && powerPresent">
            <div class="d-flex justify-content-between" v-if="activity.average_power">
              <span>{{ $t('activityBellowMPillsComponent.labelAvgPower') }}</span>
              <span>
                <b>{{ activity.average_power }}{{ ' ' + $t('generalItems.unitsWattsShort') }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.max_power">
              <span>{{ $t('activityBellowMPillsComponent.labelMaxPower') }}</span>
              <span>
                <b>{{ activity.max_power }}{{ ' ' + $t('generalItems.unitsWattsShort') }}</b>
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.normalized_power">
              <span>{{ $t('activityBellowMPillsComponent.labelNormalizedPower') }}</span>
              <span>
                <b>{{ activity.normalized_power }}{{ ' ' + $t('generalItems.unitsWattsShort') }}</b>
              </span>
            </div>
          </div>

          <div class="mt-3" v-if="graphSelection === 'cad' && cadPresent">
            <div class="d-flex justify-content-between" v-if="activity.average_cad">
              <span v-if="!activityTypeIsSwimming(activity)">
                {{ $t('activityBellowMPillsComponent.labelAvgCadence') }}
              </span>
              <span v-else>{{ $t('activityBellowMPillsComponent.labelAvgStrokeRate') }}</span>
              <span>
                <b
                  >{{ activity.average_cad
                  }}{{
                    ' ' +
                    (activityTypeIsCycling(activity)
                      ? $t('generalItems.unitsRpm')
                      : $t('generalItems.unitsSpm'))
                  }}</b
                >
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.max_cad">
              <span v-if="!activityTypeIsSwimming(activity)">
                {{ $t('activityBellowMPillsComponent.labelMaxCadence') }}
              </span>
              <span v-else>{{ $t('activityBellowMPillsComponent.labelMaxStrokeRate') }}</span>
              <span>
                <b
                  >{{ activity.max_cad
                  }}{{
                    ' ' +
                    (activityTypeIsCycling(activity)
                      ? $t('generalItems.unitsRpm')
                      : $t('generalItems.unitsSpm'))
                  }}</b
                >
              </span>
            </div>
          </div>

          <div
            class="mt-3"
            v-if="graphSelection === 'ele' && elePresent && !activityTypeIsSwimming(activity)"
          >
            <div class="d-flex justify-content-between" v-if="activity.elevation_gain">
              <span>{{ $t('activityBellowMPillsComponent.labelElevationGain') }}</span>
              <span v-if="units === 'metric'">
                <b>{{ activity.elevation_gain }}{{ ' ' + $t('generalItems.unitsM') }}</b>
              </span>
              <span v-else>
                <b
                  >{{ metersToFeet(activity.elevation_gain)
                  }}{{ ' ' + $t('generalItems.unitsFeetShort') }}</b
                >
              </span>
            </div>
            <div class="d-flex justify-content-between mt-2" v-if="activity.elevation_loss">
              <span>{{ $t('activityBellowMPillsComponent.labelElevationLoss') }}</span>
              <span v-if="units === 'metric'">
                <b>{{ activity.elevation_loss }}{{ ' ' + $t('generalItems.unitsM') }}</b>
              </span>
              <span v-else>
                <b
                  >{{ metersToFeet(activity.elevation_loss)
                  }}{{ ' ' + $t('generalItems.unitsFeetShort') }}</b
                >
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      class="tab-pane fade"
      :class="{ 'show active': !graphItems || graphItems.length === 0 }"
      id="pills-laps"
      role="tabpanel"
      aria-labelledby="pills-laps-tab"
      tabindex="1"
      v-if="activityActivityLaps && activityActivityLaps.length > 0"
    >
      <ActivityLapsComponent
        :activity="activity"
        :activityActivityLaps="activityActivityLaps"
        :units="units"
      />
    </div>

    <div
      class="tab-pane fade"
      id="pills-workout-steps"
      role="tabpanel"
      aria-labelledby="pills-workout-steps-tab"
      tabindex="2"
      v-if="activityActivityWorkoutSteps && activityActivityWorkoutSteps.length > 0"
    >
      <ActivityWorkoutStepsComponent
        :activity="activity"
        :activityActivityWorkoutSteps="activityActivityWorkoutSteps"
        :units="units"
        :activityActivityExerciseTitles="activityActivityExerciseTitles"
        :activityActivitySets="activityActivitySets"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'

// Importing the components
import ActivityLapsComponent from '@/components/Activities/ActivityLapsComponent.vue'
import ActivityStreamsLineChartComponent from '@/components/Activities/ActivityStreamsLineChartComponent.vue'
import ActivityWorkoutStepsComponent from '@/components/Activities/ActivityWorkoutStepsComponent.vue'
import BarChartComponent from '@/components/GeneralComponents/BarChartComponent.vue'
import {
  activityTypeIsCycling,
  activityTypeNotCycling,
  activityTypeIsSwimming,
  activityTypeIsSailing,
  activityTypeNotSailing,
  activityTypeIsWindsurf,
  activityTypeNotWindsurf,
  formatPace,
  formatSpeed
} from '@/utils/activityUtils'
// Import Notivue push
import { push } from 'notivue'
// Import the utils
import { getHrBarChartData, formatHrZoneLabel } from '@/utils/chartUtils'
import { formatSecondsToHoursMinutesSeconds } from '@/utils/dateTimeUtils'
import { metersToFeet } from '@/utils/unitsUtils'

// Props
const props = defineProps({
  activity: {
    type: Object,
    required: true
  },
  activityActivityLaps: {
    type: [Object, null],
    required: true
  },
  activityActivityWorkoutSteps: {
    type: [Object, null],
    required: true
  },
  activityActivityStreams: {
    type: [Object, null],
    required: true
  },
  units: {
    type: String,
    default: 'metric'
  },
  activityActivityExerciseTitles: {
    type: [Object, null],
    required: true
  },
  activityActivitySets: {
    type: [Object, null],
    required: true
  }
})

// Composables
const { t } = useI18n()

// Reactive state
const graphSelection = ref('hr')
const graphItems = ref([])
const hrPresent = ref(false)
const powerPresent = ref(false)
const elePresent = ref(false)
const cadPresent = ref(false)
const velPresent = ref(false)
const pacePresent = ref(false)
const tempPresent = ref(false)
const hrZones = ref({})

// Computed properties
const hrChartData = computed(() => getHrBarChartData(hrZones.value, t))
const formattedPace = computed(() => formatPace(t, props.activity, props.units))

// Methods
function selectGraph(type) {
  graphSelection.value = type
}

// Lifecycle
onMounted(async () => {
  try {
    if (props.activityActivityStreams && props.activityActivityStreams.length > 0) {
      // Check if the activity has the streams
      for (const element of props.activityActivityStreams) {
        if (element.stream_type === 1) {
          hrPresent.value = true
          graphItems.value.push({
            type: 'hr',
            label: `${t('activityMandAbovePillsComponent.labelGraphHR')}`
          })
          // If HR zones are present, add them to the hrZones object
          const hrStream = props.activityActivityStreams.find(
            (stream) => stream.zone_percentages?.hr
          )
          hrZones.value = hrStream?.zone_percentages?.hr ?? {}
          if (hrZones.value && Object.keys(hrZones.value).length > 0) {
            hrPresent.value = true
            graphItems.value.push({
              type: 'hrZones',
              label: `${t('activityMandAbovePillsComponent.labelHRZones')}`
            })
          }
        }
        if (element.stream_type === 2) {
          powerPresent.value = true
          graphItems.value.push({
            type: 'power',
            label: `${t('activityMandAbovePillsComponent.labelGraphPower')}`
          })
        }
        if (element.stream_type === 3) {
          cadPresent.value = true
          // Label as "Stroke Rate" over "Cadence" for swimming activities
          if (activityTypeIsSwimming(props.activity)) {
            graphItems.value.push({
              type: 'cad',
              label: `${t('activityMandAbovePillsComponent.labelGraphStrokeRate')}`
            })
          } else {
            graphItems.value.push({
              type: 'cad',
              label: `${t('activityMandAbovePillsComponent.labelGraphCadence')}`
            })
          }
        }
        if (element.stream_type === 4) {
          // Do not show elevation for swimming activities
          if (!activityTypeIsSwimming(props.activity)) {
            elePresent.value = true
            graphItems.value.push({
              type: 'ele',
              label: `${t('activityMandAbovePillsComponent.labelGraphElevation')}`
            })
          }
        }
        if (element.stream_type === 5) {
          velPresent.value = true
          if (
            activityTypeIsCycling(props.activity) ||
            activityTypeIsSailing(props.activity) ||
            activityTypeIsWindsurf(props.activity)
          ) {
            graphItems.value.push({
              type: 'vel',
              label: `${t('activityMandAbovePillsComponent.labelGraphVelocity')}`
            })
          }
        }
        if (element.stream_type === 6) {
          pacePresent.value = true
          if (
            activityTypeNotCycling(props.activity) &&
            activityTypeNotSailing(props.activity) &&
            activityTypeNotWindsurf(props.activity)
          ) {
            graphItems.value.push({
              type: 'pace',
              label: `${t('activityMandAbovePillsComponent.labelGraphPace')}`
            })
          }
        }
        if (element.stream_type === 8) {
          tempPresent.value = true
          graphItems.value.push({
            type: 'temp',
            label: t('generalItems.labelTemperature')
          })
        }
      }
    }
    if (graphItems.value.length > 0) {
      graphSelection.value = graphItems.value[0].type
    }
  } catch (error) {
    // If there is an error, set the error message and show the error alert.
    push.error(
      `${t('activityMandAbovePillsComponent.errorMessageProcessingActivityStreams')} - ${error}`
    )
  }
})
</script>
