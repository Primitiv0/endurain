#!/bin/sh

set -e

echo_info_log() {
    echo "INFO:     $1"
}

echo_error_log() {
    echo "ERROR:     $1" >&2
}

# Log the container's UID for troubleshooting
current_uid=$(id -u)
echo_info_log "Container running as UID $current_uid"

# Create required directories
BACKEND_FOLDER="${BACKEND_DIR:-/app/backend}"
DATA_FOLDER="${DATA_DIR:-$BACKEND_FOLDER/data}"
LOGS_FOLDER="${LOGS_DIR:-$BACKEND_FOLDER/logs}"
FRONTEND_FOLDER="${FRONTEND_DIR:-/app/frontend/dist}"

REQUIRED_DIRS="
$DATA_FOLDER
$DATA_FOLDER/user_images
$DATA_FOLDER/server_images
$DATA_FOLDER/activity_media
$DATA_FOLDER/activity_thumbnails
$DATA_FOLDER/activity_files
$DATA_FOLDER/activity_files/processed
$DATA_FOLDER/activity_files/bulk_import
$DATA_FOLDER/activity_files/bulk_import/import_errors
$DATA_FOLDER/activity_files/strava_import
$DATA_FOLDER/activity_files/strava_import/activities
$DATA_FOLDER/activity_files/strava_import/media
$DATA_FOLDER/activity_files/strava_import/import_errors
$LOGS_FOLDER
"

for dir in $REQUIRED_DIRS; do
    if [ ! -d "$dir" ]; then
        echo_info_log "Creating directory: $dir"
        if ! mkdir -p "$dir" 2>/dev/null; then
            echo_error_log "Cannot create $dir - permission denied."
            echo_error_log "Container UID: $current_uid"
            if echo "$dir" | grep -q "^$LOGS_FOLDER"; then
                mount_root="$LOGS_FOLDER"
            else
                mount_root="$DATA_FOLDER"
            fi
            if [ -d "$mount_root" ]; then
                echo_error_log "Mount point: $(stat -c '%A  owner=%u  group=%g  path=%n' "$mount_root" 2>/dev/null || true)"
            fi
            echo_error_log "The bind mount on the host is not writable by container UID $current_uid."
            echo_error_log "Fix on the host - run once:"
            echo_error_log "  sudo chown -R $current_uid:$current_uid /var/opt/endurain/backend"
            echo_error_log "(Replace /var/opt/endurain with your LOCAL_PATH if set.)"
            echo_error_log "See docs.endurain.com/getting-started#create-directory-structure"
            exit 1
        fi
    fi
done

if [ -n "$ENDURAIN_HOST" ]; then
    echo "window.env = { ENDURAIN_HOST: \"$ENDURAIN_HOST\" };" > "$FRONTEND_FOLDER/env.js"
    echo_info_log "Runtime env.js written with ENDURAIN_HOST=$ENDURAIN_HOST"
fi

# Set log level (default: info)
# Supported levels: critical, error, warning, info, debug, trace
LOG_LEVEL="${LOG_LEVEL:-info}"

# Validate log level
case "$LOG_LEVEL" in
    critical|error|warning|info|debug|trace)
        # Valid log level
        ;;
    *)
        echo_error_log "Invalid LOG_LEVEL '$LOG_LEVEL'. Supported levels: critical, error, warning, info, debug, trace. Defaulting to 'info'."
        LOG_LEVEL="info"
        ;;
esac

echo_info_log "Starting FastAPI with BEHIND_PROXY=$BEHIND_PROXY, LOG_LEVEL=$LOG_LEVEL"

CMD="uvicorn main:app --host 0.0.0.0 --port 8080 --log-level $LOG_LEVEL"
if [ "$BEHIND_PROXY" = "true" ]; then
    CMD="$CMD --proxy-headers"
fi

exec $CMD