#!/bin/bash

echo "=== CORRECTED AI EVALUATION DOUBLE-RUN ANALYSIS ==="
echo "Timestamp: $(date)"
echo

echo "1. ALL RECENT EVALUATION LOGS (last 24h)"
echo "=========================================="
if [ -d "projects_log" ]; then
    echo "All batch logs with timestamps:"
    ls -la projects_log/batch_run_*.log | sort -k8,9
    echo
    
    echo "Checking for logs created within 10 seconds of each other:"
    ls -la projects_log/batch_run_*.log | awk '{print $8 " " $9}' | sort | awk '
    {
        split($2, time_parts, "_")
        timestamp = time_parts[1] " " time_parts[2]
        split(time_parts[2], time_digits, "")
        hour = time_digits[1] time_digits[2]
        min = time_digits[3] time_digits[4]  
        sec = time_digits[5] time_digits[6]
        total_seconds = hour * 3600 + min * 60 + sec
        print total_seconds, $0
    }' | sort -n | awk '
    NR > 1 {
        diff = $1 - prev
        if (diff <= 10 && diff >= 0) {
            print "⚠️  CLOSE TIMESTAMPS DETECTED:"
            print "  Previous:", prev_line
            print "  Current: ", $2 " " $3
            print "  Difference:", diff, "seconds"
            print ""
        }
    }
    { prev = $1; prev_line = $2 " " $3 }'
fi
echo

echo "2. CHECKING FOR CONCURRENT PROCESSES"
echo "===================================="
ps aux | grep -E "(python|evaluate_projects|main\.py)" | grep -v grep
echo

echo "3. CHECKING SCHEDULER JOBS"
echo "=========================="
# Check if there are any cron jobs or scheduled tasks
crontab -l 2>/dev/null || echo "No crontab found"
echo

echo "4. CHECKING SERVER LOGS FOR DUPLICATE API CALLS"
echo "==============================================="
# Look for Flask server logs that might show duplicate API calls
find . -name "*.log" -o -name "*log*" | grep -v projects_log | head -10
echo

echo "5. CHECKING DOCKER CONTAINER LOGS"
echo "================================="
# If running in Docker, check container logs
if [ -f "/.dockerenv" ]; then
    echo "Docker container detected. Recent container logs:"
    # This would need to be run from host: docker logs <container_name> --tail 50
    echo "Run from host: docker logs \$(docker ps -q) --tail 50"
fi
echo

echo "6. CHECKING FOR MULTIPLE CONTAINER INSTANCES"
echo "============================================"
# Check if multiple containers are running
echo "Run from host: docker ps --filter ancestor=<your_image>"
echo

echo "7. ANALYSIS OF LOG CONTENT PATTERNS"
echo "==================================="
if [ -d "projects_log" ]; then
    echo "Checking if same projects are being evaluated multiple times:"
    # Get the most recent two logs
    RECENT_LOGS=$(ls -t projects_log/batch_run_*.log | head -2)
    if [ $(echo "$RECENT_LOGS" | wc -l) -eq 2 ]; then
        LOG1=$(echo "$RECENT_LOGS" | sed -n '1p')
        LOG2=$(echo "$RECENT_LOGS" | sed -n '2p')
        
        echo "Comparing $LOG1 and $LOG2:"
        echo "Projects in first log:"
        grep "Processing:" "$LOG1" | head -5
        echo
        echo "Projects in second log:"  
        grep "Processing:" "$LOG2" | head -5
        echo
        
        # Check if they processed the same projects
        PROJECTS1=$(grep "Processing:" "$LOG1" | wc -l)
        PROJECTS2=$(grep "Processing:" "$LOG2" | wc -l)
        echo "Projects processed in first run: $PROJECTS1"
        echo "Projects processed in second run: $PROJECTS2"
    fi
fi