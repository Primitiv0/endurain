from pydantic import BaseModel


class Activity(BaseModel):
    """
    Schema representing a fitness activity.

    Attributes:
        id: Unique activity identifier.
        user_id: ID of the owning user.
        description: Public activity description.
        private_notes: Private notes visible only to owner.
        distance: Total distance in meters.
        name: Activity name.
        activity_type: Numeric code for the sport type.
        start_time: Activity start time (UTC).
        start_time_tz_applied: Start time with timezone applied.
        end_time: Activity end time (UTC).
        end_time_tz_applied: End time with timezone applied.
        timezone: IANA timezone string.
        total_elapsed_time: Total elapsed wall-clock time
            in seconds.
        total_timer_time: Active timer time in seconds.
        city: City where the activity took place.
        town: Town where the activity took place.
        country: Country where the activity took place.
        created_at: Record creation timestamp (UTC).
        created_at_tz_applied: Creation time with timezone
            applied.
        elevation_gain: Total elevation gain in meters.
        elevation_loss: Total elevation loss in meters.
        pace: Average pace in seconds per kilometer.
        average_speed: Average speed in meters per second.
        max_speed: Maximum speed in meters per second.
        average_power: Average power output in watts.
        max_power: Maximum power output in watts.
        normalized_power: Normalized power in watts.
        average_hr: Average heart rate in bpm.
        max_hr: Maximum heart rate in bpm.
        average_cad: Average cadence in rpm/spm.
        max_cad: Maximum cadence in rpm/spm.
        workout_feeling: Subjective feeling rating.
        workout_rpe: Rate of perceived exertion.
        calories: Estimated calories burned.
        visibility: Visibility level of the activity.
        gear_id: Associated gear identifier.
        strava_gear_id: Strava gear identifier.
        strava_activity_id: Strava activity identifier.
        garminconnect_activity_id: Garmin Connect activity
            identifier.
        garminconnect_gear_id: Garmin Connect gear identifier.
        import_info: Import metadata with keys: imported
            (bool), import_source (str),
            import_ISO_time (str).
        is_hidden: Whether the activity is hidden.
        hide_start_time: Hide the start time from others.
        hide_location: Hide location data from others.
        hide_map: Hide the map from others.
        hide_hr: Hide heart rate data from others.
        hide_power: Hide power data from others.
        hide_cadence: Hide cadence data from others.
        hide_elevation: Hide elevation data from others.
        hide_speed: Hide speed data from others.
        hide_pace: Hide pace data from others.
        hide_laps: Hide lap data from others.
        hide_workout_sets_steps: Hide workout sets and steps.
        hide_gear: Hide gear information from others.
        tracker_manufacturer: Device manufacturer name.
        tracker_model: Device model name.
        map_thumbnail_path: Path to the map thumbnail image.
    """

    id: int | None = None
    user_id: int | None = None
    description: str | None = None
    private_notes: str | None = None
    distance: int
    name: str
    activity_type: int
    start_time: str | None = None
    start_time_tz_applied: str | None = None
    end_time: str | None = None
    end_time_tz_applied: str | None = None
    timezone: str | None = None
    total_elapsed_time: float | None = None
    total_timer_time: float | None = None
    city: str | None = None
    town: str | None = None
    country: str | None = None
    created_at: str | None = None
    created_at_tz_applied: str | None = None
    elevation_gain: int | None = None
    elevation_loss: int | None = None
    pace: float | None = None
    average_speed: float | None = None
    max_speed: float | None = None
    average_power: int | None = None
    max_power: int | None = None
    normalized_power: int | None = None
    average_hr: int | None = None
    max_hr: int | None = None
    average_cad: int | None = None
    max_cad: int | None = None
    workout_feeling: int | None = None
    workout_rpe: int | None = None
    calories: int | None = None
    visibility: int | None = None
    gear_id: int | None = None
    strava_gear_id: str | None = None
    strava_activity_id: int | None = None
    garminconnect_activity_id: int | None = None
    garminconnect_gear_id: str | None = None
    import_info: dict | None = None
    is_hidden: bool = False
    hide_start_time: bool | None = None
    hide_location: bool | None = None
    hide_map: bool | None = None
    hide_hr: bool | None = None
    hide_power: bool | None = None
    hide_cadence: bool | None = None
    hide_elevation: bool | None = None
    hide_speed: bool | None = None
    hide_pace: bool | None = None
    hide_laps: bool | None = None
    hide_workout_sets_steps: bool | None = None
    hide_gear: bool | None = None
    tracker_manufacturer: str | None = None
    tracker_model: str | None = None
    map_thumbnail_path: str | None = None

    model_config = {"from_attributes": True}


class ActivitySportStats(BaseModel):
    """Aggregated stats for a single sport type over a timeframe."""

    distance: float = 0.0
    time: float = 0.0
    calories: float = 0.0


class ActivityStats(BaseModel):
    """Per-sport aggregated stats for a timeframe (week or month)."""

    run: ActivitySportStats = ActivitySportStats()
    bike: ActivitySportStats = ActivitySportStats()
    swim: ActivitySportStats = ActivitySportStats()
    walk: ActivitySportStats = ActivitySportStats()
    hike: ActivitySportStats = ActivitySportStats()
    rowing: ActivitySportStats = ActivitySportStats()
    snow_ski: ActivitySportStats = ActivitySportStats()
    snowboard: ActivitySportStats = ActivitySportStats()
    windsurf: ActivitySportStats = ActivitySportStats()
    stand_up_paddleboarding: ActivitySportStats = ActivitySportStats()
    surfing: ActivitySportStats = ActivitySportStats()
    kayaking: ActivitySportStats = ActivitySportStats()
    sailing: ActivitySportStats = ActivitySportStats()
    snowshoeing: ActivitySportStats = ActivitySportStats()
    inline_skating: ActivitySportStats = ActivitySportStats()


class ActivityEdit(BaseModel):
    id: int
    description: str | None = None
    private_notes: str | None = None
    name: str
    activity_type: int
    visibility: int | None = None
    is_hidden: bool | None = None
    gear_id: int | None = None
    hide_start_time: bool | None = None
    hide_location: bool | None = None
    hide_map: bool | None = None
    hide_hr: bool | None = None
    hide_power: bool | None = None
    hide_cadence: bool | None = None
    hide_elevation: bool | None = None
    hide_speed: bool | None = None
    hide_pace: bool | None = None
    hide_laps: bool | None = None
    hide_workout_sets_steps: bool | None = None
    hide_gear: bool | None = None
