#!/usr/bin/env python3
"""
Test script to create the MVP schedules for the job application workflow
"""

import requests
import json
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:8002/api/v1"

def create_weekday_schedule():
    """Create weekday hourly schedule (8-23, Mon-Fri)"""
    schedule_data = {
        "name": "Weekday Full Workflow",
        "description": "Run full workflow every hour between 8-23 on weekdays",
        "workflow_type": "main",
        "parameters": {
            "number": 10,
            "regions": ["germany", "austria"]
        },
        "cron_schedule": "0 8-23 * * 1-5",  # Every hour 8-23, Mon-Fri
        "timezone": "Europe/Berlin"
    }

    response = requests.post(f"{BASE_URL}/schedules", json=schedule_data)
    print(f"Weekday Schedule Creation: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Created: {result['name']} (ID: {result['id']})")
        print(f"   Next run: {result.get('next_run', 'Not scheduled')}")
    else:
        print(f"❌ Failed: {response.text}")
    return response.status_code == 201

def create_weekend_schedule():
    """Create weekend 3x daily schedule (Sat-Sun)"""
    schedule_data = {
        "name": "Weekend 3x Daily Full Workflow",
        "description": "Run full workflow 3 times a day on weekends",
        "workflow_type": "main",
        "parameters": {
            "number": 15,
            "regions": ["germany", "austria", "switzerland"]
        },
        "cron_schedule": "0 9,15,21 * * 6,0",  # 9am, 3pm, 9pm on Sat-Sun
        "timezone": "Europe/Berlin"
    }

    response = requests.post(f"{BASE_URL}/schedules", json=schedule_data)
    print(f"Weekend Schedule Creation: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Created: {result['name']} (ID: {result['id']})")
        print(f"   Next run: {result.get('next_run', 'Not scheduled')}")
    else:
        print(f"❌ Failed: {response.text}")
    return response.status_code == 201

def list_schedules():
    """List all schedules"""
    response = requests.get(f"{BASE_URL}/schedules")
    print(f"\n📋 Current Schedules: {response.status_code}")
    if response.status_code == 200:
        schedules = response.json()
        print(f"Total schedules: {len(schedules)}")
        for schedule in schedules:
            status = "✅ Enabled" if schedule.get('enabled', False) else "⏸️ Disabled"
            next_run = schedule.get('next_run', 'Not scheduled')
            print(f"  • {schedule['name']} ({status})")
            print(f"    Next: {next_run}")
            print(f"    Cron: {schedule['cron_schedule']}")
    else:
        print(f"❌ Failed: {response.text}")

def get_scheduler_status():
    """Get scheduler status"""
    response = requests.get(f"{BASE_URL}/schedules/status")
    print(f"\n📊 Scheduler Status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        running = "✅ Running" if status.get('running', False) else "❌ Stopped"
        print(f"Scheduler: {running}")
        print(f"Total schedules: {status.get('total_schedules', 0)}")
        print(f"Enabled schedules: {status.get('enabled_schedules', 0)}")
        print(f"Active jobs: {status.get('active_jobs', 0)}")

        next_job = status.get('next_job')
        if next_job:
            print(f"Next job: {next_job['name']} at {next_job['next_run_time']}")
    else:
        print(f"❌ Failed: {response.text}")

def main():
    """Main test function"""
    print("🧪 Testing Job Application Workflow Scheduling System")
    print("=" * 60)

    # Test scheduler status
    get_scheduler_status()

    # Create weekday schedule
    print("\n📅 Creating Weekday Schedule...")
    weekday_success = create_weekday_schedule()

    # Create weekend schedule
    print("\n📅 Creating Weekend Schedule...")
    weekend_success = create_weekend_schedule()

    # List all schedules
    list_schedules()

    # Final status
    get_scheduler_status()

    print("\n" + "=" * 60)
    if weekday_success and weekend_success:
        print("🎉 SUCCESS: Both schedules created successfully!")
        print("📋 Your schedules are now active and will run automatically.")
        print("🔧 You can manage them via the web interface at http://localhost:8002")
    else:
        print("⚠️ Some schedules failed to create. Check the server logs.")

if __name__ == "__main__":
    main()