#!/usr/bin/env bash
# Colors
SUCCESS="\e[0;32m" # Green
ERROR="\e[0;31m"   # Red
NC="\e[0m"         # No Color

# Logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$(date '+%Y%m%d-%H%M%S')-pipeline.log"

# Print to terminal AND log file
log() { echo -e "$@" | tee -a "$LOG_FILE"; }

log "Pipeline started at $(date)"
log "Log file: $LOG_FILE"
log ""

cd initialization
log "Downloading models..."
uv run load_models.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Models are downloaded and ready.${NC}"
else
    log "${ERROR}Error downloading models. Please check the logs for details!${NC}"
    exit 1
fi

cd ../scraping
log "Fetching data..."
uv run fetch_data.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data fetched successfully.${NC}"
else
    log "${ERROR}Error downloading data!${NC}"
    exit 1
fi

cd ../normalization
log "Normalizing data..."
uv run normalize_data.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data normalized successfully.${NC}"
else
    log "${ERROR}Error normalizing data!${NC}"
    exit 1
fi

cd ../summarization
log "Summarizing data..."
uv run summarize_data.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data summarized successfully.${NC}"
else
    log "${ERROR}Error summarizing data!${NC}"
    exit 1
fi

cd ../extraction
log "Extracting data..."
uv run extract_data.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data extracted successfully.${NC}"
else
    log "${ERROR}Error extracting data!${NC}"
    exit 1
fi

cd ../embedding
log "Embedding data..."
uv run embed_data.py >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data embedded successfully.${NC}"
else
    log "${ERROR}Error embedding data!${NC}"
    exit 1
fi

cd ../storage
log "Storing data..."
uv run store_data.py --create-tables >>"$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    log "${SUCCESS}Data stored successfully.${NC}"
else
    log "${ERROR}Error storing data!${NC}"
    exit 1
fi

log ""
log "Pipeline finished at $(date)"
