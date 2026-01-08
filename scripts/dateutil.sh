#!/bin/bash
# Date Utility Script for cronk-personal-life agents
# Handles date calculations with EST timezone awareness
#
# Usage:
#   dateutil.sh now                    - Print current date/time with day of week
#   dateutil.sh day YYYY-MM-DD         - Get day of week for a date
#   dateutil.sh diff YYYY-MM-DD YYYY-MM-DD - Days between two dates
#   dateutil.sh range YYYY-MM-DD YYYY-MM-DD - List all dates in range with days
#   dateutil.sh until YYYY-MM-DD       - Days from today until date

set -o pipefail

# Force EST/EDT timezone (Philadelphia)
export TZ="America/New_York"

usage() {
    echo "Date Utility Script for cronk-personal-life"
    echo ""
    echo "Usage:"
    echo "  dateutil.sh now                        - Current date/time with day of week"
    echo "  dateutil.sh day YYYY-MM-DD             - Day of week for a date"
    echo "  dateutil.sh diff YYYY-MM-DD YYYY-MM-DD - Days between two dates"
    echo "  dateutil.sh range YYYY-MM-DD YYYY-MM-DD - List dates in range with days"
    echo "  dateutil.sh until YYYY-MM-DD           - Days from today until date"
    echo ""
    echo "All dates use America/New_York timezone (EST/EDT)"
}

# Get current date/time with day of week
cmd_now() {
    echo "Current Date/Time (EST): $(date '+%A, %B %d, %Y at %I:%M %p %Z')"
    echo "ISO Format: $(date '+%Y-%m-%d')"
}

# Get day of week for a specific date
cmd_day() {
    local input_date="$1"
    if [ -z "$input_date" ]; then
        echo "Error: Please provide a date in YYYY-MM-DD format"
        exit 1
    fi
    
    # Validate date format
    if ! [[ "$input_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "Error: Date must be in YYYY-MM-DD format"
        exit 1
    fi
    
    # macOS date command syntax
    local result=$(date -j -f "%Y-%m-%d" "$input_date" "+%A, %B %d, %Y" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "Error: Invalid date '$input_date'"
        exit 1
    fi
    
    echo "$input_date is $result"
}

# Calculate days between two dates
cmd_diff() {
    local date1="$1"
    local date2="$2"
    
    if [ -z "$date1" ] || [ -z "$date2" ]; then
        echo "Error: Please provide two dates in YYYY-MM-DD format"
        exit 1
    fi
    
    # Convert to epoch seconds (macOS)
    local epoch1=$(date -j -f "%Y-%m-%d" "$date1" "+%s" 2>/dev/null)
    local epoch2=$(date -j -f "%Y-%m-%d" "$date2" "+%s" 2>/dev/null)
    
    if [ -z "$epoch1" ] || [ -z "$epoch2" ]; then
        echo "Error: Invalid date format"
        exit 1
    fi
    
    local diff=$(( (epoch2 - epoch1) / 86400 ))
    
    if [ $diff -ge 0 ]; then
        echo "$diff days from $date1 to $date2"
    else
        echo "$(( -diff )) days from $date2 to $date1"
    fi
}

# List all dates in a range with their days of week
cmd_range() {
    local start_date="$1"
    local end_date="$2"
    
    if [ -z "$start_date" ] || [ -z "$end_date" ]; then
        echo "Error: Please provide start and end dates in YYYY-MM-DD format"
        exit 1
    fi
    
    # Convert to epoch seconds
    local epoch_start=$(date -j -f "%Y-%m-%d" "$start_date" "+%s" 2>/dev/null)
    local epoch_end=$(date -j -f "%Y-%m-%d" "$end_date" "+%s" 2>/dev/null)
    
    if [ -z "$epoch_start" ] || [ -z "$epoch_end" ]; then
        echo "Error: Invalid date format"
        exit 1
    fi
    
    echo "Date Range: $start_date to $end_date"
    echo "---"
    
    local current=$epoch_start
    while [ $current -le $epoch_end ]; do
        date -j -f "%s" "$current" "+%Y-%m-%d (%A)"
        current=$((current + 86400))
    done
}

# Days until a specific date from today
cmd_until() {
    local target_date="$1"
    
    if [ -z "$target_date" ]; then
        echo "Error: Please provide a date in YYYY-MM-DD format"
        exit 1
    fi
    
    local today=$(date "+%Y-%m-%d")
    local epoch_today=$(date "+%s")
    local epoch_target=$(date -j -f "%Y-%m-%d" "$target_date" "+%s" 2>/dev/null)
    
    if [ -z "$epoch_target" ]; then
        echo "Error: Invalid date '$target_date'"
        exit 1
    fi
    
    local diff=$(( (epoch_target - epoch_today) / 86400 ))
    local day_name=$(date -j -f "%Y-%m-%d" "$target_date" "+%A" 2>/dev/null)
    
    if [ $diff -gt 0 ]; then
        echo "$diff days until $target_date ($day_name)"
    elif [ $diff -eq 0 ]; then
        echo "$target_date is today! ($day_name)"
    else
        echo "$target_date was $(( -diff )) days ago ($day_name)"
    fi
}

# Main command dispatch
case "$1" in
    now)
        cmd_now
        ;;
    day)
        cmd_day "$2"
        ;;
    diff)
        cmd_diff "$2" "$3"
        ;;
    range)
        cmd_range "$2" "$3"
        ;;
    until)
        cmd_until "$2"
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
