#!/usr/bin/env python3
"""
Scheduler Manager for Bewerbungs-Bot
APScheduler integration for automated workflow execution
"""

import os
import json
import uuid
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SCHEDULES_FILE = Path("data/schedules.json")
DEFAULT_TIMEZONE = timezone('Europe/Berlin')
JOB_TIMEOUT_SECONDS = 1800  # 30 minutes timeout

@dataclass
class ExecutionResult:
    """Result of a scheduled job execution"""
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "running"  # running, success, failed, timeout
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None

@dataclass
class Schedule:
    """Schedule configuration"""
    id: str
    name: str
    description: str
    enabled: bool
    workflow_type: str  # main, evaluate, generate, email_ingest, rss_ingest
    parameters: Dict[str, Any]
    cron_schedule: str
    timezone: str
    created_at: str
    updated_at: str
    last_run: Optional[str] = None
    last_status: Optional[str] = None
    execution_history: List[ExecutionResult] = None

    def __post_init__(self):
        if self.execution_history is None:
            self.execution_history = []

class SchedulerManager:
    """Manages scheduled jobs using APScheduler"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.schedules: Dict[str, Schedule] = {}
        self.scheduler = None
        self._setup_scheduler()
        self._load_schedules()

    def _setup_scheduler(self):
        """Initialize APScheduler with proper configuration"""
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': {'type': 'threadpool', 'max_workers': 2}
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 30
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=DEFAULT_TIMEZONE
        )

        logger.info("Scheduler initialized")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

    def _load_schedules(self):
        """Load schedules from JSON file"""
        try:
            if SCHEDULES_FILE.exists():
                with open(SCHEDULES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for schedule_data in data.get('schedules', []):
                    try:
                        # Convert execution_history back to ExecutionResult objects
                        history = []
                        for hist_data in schedule_data.get('execution_history', []):
                            history.append(ExecutionResult(**hist_data))

                        schedule_data['execution_history'] = history
                        schedule = Schedule(**schedule_data)
                        self.schedules[schedule.id] = schedule

                        # Add to scheduler if enabled
                        if schedule.enabled:
                            self._add_schedule_to_scheduler(schedule)

                    except Exception as e:
                        logger.error(f"Error loading schedule {schedule_data.get('id', 'unknown')}: {e}")

                logger.info(f"Loaded {len(self.schedules)} schedules")

        except Exception as e:
            logger.error(f"Error loading schedules file: {e}")
            # Create empty schedules file if it doesn't exist or is corrupted
            self._save_schedules()

    def _save_schedules(self):
        """Save schedules to JSON file"""
        try:
            SCHEDULES_FILE.parent.mkdir(exist_ok=True)

            # Convert schedules to dict format
            schedules_data = []
            for schedule in self.schedules.values():
                schedule_dict = asdict(schedule)
                # Convert ExecutionResult objects to dicts
                schedule_dict['execution_history'] = [
                    asdict(result) for result in schedule.execution_history
                ]
                schedules_data.append(schedule_dict)

            data = {
                'schedules': schedules_data,
                'last_updated': datetime.now().isoformat()
            }

            with open(SCHEDULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(schedules_data)} schedules")

        except Exception as e:
            logger.error(f"Error saving schedules: {e}")

    def create_schedule(self, name: str, description: str, workflow_type: str,
                       parameters: Dict[str, Any], cron_schedule: str,
                       timezone: str = "Europe/Berlin") -> Schedule:
        """Create a new schedule"""
        schedule_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        schedule = Schedule(
            id=schedule_id,
            name=name,
            description=description,
            enabled=True,
            workflow_type=workflow_type,
            parameters=parameters,
            cron_schedule=cron_schedule,
            timezone=timezone,
            created_at=now,
            updated_at=now
        )

        self.schedules[schedule_id] = schedule
        self._add_schedule_to_scheduler(schedule)
        self._save_schedules()

        logger.info(f"Created schedule: {name} ({schedule_id})")
        return schedule

    def update_schedule(self, schedule_id: str, **updates) -> Optional[Schedule]:
        """Update an existing schedule"""
        if schedule_id not in self.schedules:
            return None

        schedule = self.schedules[schedule_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        schedule.updated_at = datetime.now().isoformat()

        # Remove from scheduler and re-add if enabled
        self._remove_schedule_from_scheduler(schedule_id)
        if schedule.enabled:
            self._add_schedule_to_scheduler(schedule)

        self._save_schedules()
        logger.info(f"Updated schedule: {schedule.name} ({schedule_id})")
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        if schedule_id not in self.schedules:
            return False

        schedule = self.schedules[schedule_id]

        # Remove from scheduler
        self._remove_schedule_from_scheduler(schedule_id)

        # Remove from storage
        del self.schedules[schedule_id]
        self._save_schedules()

        logger.info(f"Deleted schedule: {schedule.name} ({schedule_id})")
        return True

    def toggle_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Enable/disable a schedule"""
        if schedule_id not in self.schedules:
            return None

        schedule = self.schedules[schedule_id]
        schedule.enabled = not schedule.enabled
        schedule.updated_at = datetime.now().isoformat()

        if schedule.enabled:
            self._add_schedule_to_scheduler(schedule)
        else:
            self._remove_schedule_from_scheduler(schedule_id)

        self._save_schedules()
        logger.info(f"Toggled schedule: {schedule.name} ({schedule_id}) -> {'enabled' if schedule.enabled else 'disabled'}")
        return schedule

    def run_schedule_now(self, schedule_id: str) -> Optional[str]:
        """Run a schedule immediately"""
        if schedule_id not in self.schedules:
            return None

        schedule = self.schedules[schedule_id]
        job_id = f"job_{schedule_id}"

        # Check if job is already running
        if self.scheduler.get_job(job_id):
            # Job exists, trigger it
            self.scheduler.modify_job(job_id, next_run_time=datetime.now())
            logger.info(f"Triggered immediate run for schedule: {schedule.name}")
            return f"Triggered run for {schedule.name}"
        else:
            # Job doesn't exist, add it temporarily
            self._add_schedule_to_scheduler(schedule)
            logger.info(f"Added and triggered schedule: {schedule.name}")
            return f"Added and triggered {schedule.name}"

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a specific schedule"""
        return self.schedules.get(schedule_id)

    def list_schedules(self) -> List[Schedule]:
        """Get all schedules"""
        return list(self.schedules.values())

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status information"""
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })

        return {
            'running': self.scheduler.running if self.scheduler else False,
            'total_schedules': len(self.schedules),
            'enabled_schedules': len([s for s in self.schedules.values() if s.enabled]),
            'active_jobs': len(jobs),
            'jobs': jobs
        }

    def _add_schedule_to_scheduler(self, schedule: Schedule):
        """Add a schedule to the APScheduler"""
        try:
            job_id = f"job_{schedule.id}"

            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            # Create trigger
            trigger = CronTrigger.from_crontab(
                schedule.cron_schedule,
                timezone=timezone(schedule.timezone)
            )

            # Add job
            self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                id=job_id,
                name=schedule.name,
                args=[schedule.id],
                max_instances=1
            )

            logger.debug(f"Added job to scheduler: {schedule.name} ({job_id})")

        except Exception as e:
            logger.error(f"Error adding schedule to scheduler: {schedule.name} - {e}")

    def _remove_schedule_from_scheduler(self, schedule_id: str):
        """Remove a schedule from the APScheduler"""
        try:
            job_id = f"job_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.debug(f"Removed job from scheduler: {job_id}")
        except Exception as e:
            logger.error(f"Error removing schedule from scheduler: {schedule_id} - {e}")

    def _validate_provider_config(self, workflow_type: str, parameters: Dict[str, Any]) -> bool:
        """Validate provider configuration for ingestion workflows"""
        if workflow_type not in ("email_ingest", "rss_ingest"):
            return True  # No validation needed for other workflows

        provider = parameters.get("provider")
        if not provider:
            logger.error(f"Provider not specified for {workflow_type}")
            return False

        # Try to load config and check provider
        try:
            # Import here to avoid circular imports
            from application_generator import load_application_config
            config = load_application_config("config.yaml")

            providers = config.get("providers", {})
            if provider not in providers:
                logger.error(f"Provider '{provider}' not found in configuration")
                return False

            if not providers[provider].get("enabled", False):
                logger.error(f"Provider '{provider}' is disabled in configuration")
                return False

            # Check if the channel is configured
            channel = parameters.get("channel", "email" if workflow_type == "email_ingest" else "rss")
            provider_config = providers[provider]
            if "channels" not in provider_config or channel not in provider_config["channels"]:
                logger.error(f"Channel '{channel}' not configured for provider '{provider}'")
                return False

            logger.debug(f"Provider '{provider}' validation passed for {workflow_type}")
            return True

        except Exception as e:
            logger.error(f"Error validating provider config: {e}")
            return False

    def _execute_workflow(self, schedule_id: str):
        """Execute a workflow job"""
        if schedule_id not in self.schedules:
            logger.error(f"Schedule not found: {schedule_id}")
            return

        schedule = self.schedules[schedule_id]
        run_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Create execution result
        result = ExecutionResult(
            run_id=run_id,
            started_at=started_at,
            status="running"
        )

        # Add to execution history
        schedule.execution_history.insert(0, result)  # Add to beginning
        schedule.last_run = started_at
        schedule.last_status = "running"

        # Keep only last 10 executions
        if len(schedule.execution_history) > 10:
            schedule.execution_history = schedule.execution_history[:10]

        self._save_schedules()

        logger.info(f"Starting workflow execution: {schedule.name} (run: {run_id})")

        try:
            # Validate provider config for ingestion workflows
            if not self._validate_provider_config(schedule.workflow_type, schedule.parameters):
                result.status = "failed"
                result.completed_at = datetime.now().isoformat()
                result.error = "Provider validation failed"
                schedule.last_status = "failed"
                self._save_schedules()
                return

            # Build command
            command = self._build_workflow_command(schedule.workflow_type, schedule.parameters)

            # Execute command
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )

            try:
                stdout, stderr = process.communicate(timeout=JOB_TIMEOUT_SECONDS)

                # Update result
                result.completed_at = datetime.now().isoformat()
                result.exit_code = process.returncode
                result.output = stdout
                result.error = stderr

                if process.returncode == 0:
                    result.status = "success"
                    schedule.last_status = "success"
                    logger.info(f"Workflow completed successfully: {schedule.name}")
                else:
                    result.status = "failed"
                    schedule.last_status = "failed"
                    logger.error(f"Workflow failed: {schedule.name} (exit code: {process.returncode})")

            except subprocess.TimeoutExpired:
                process.kill()
                result.status = "timeout"
                result.completed_at = datetime.now().isoformat()
                result.error = f"Job timed out after {JOB_TIMEOUT_SECONDS} seconds"
                schedule.last_status = "timeout"
                logger.error(f"Workflow timed out: {schedule.name}")

        except Exception as e:
            result.status = "failed"
            result.completed_at = datetime.now().isoformat()
            result.error = str(e)
            schedule.last_status = "failed"
            logger.error(f"Workflow execution error: {schedule.name} - {e}")

        # Save updated schedule
        schedule.updated_at = datetime.now().isoformat()
        self._save_schedules()

    def _build_workflow_command(self, workflow_type: str, parameters: Dict[str, Any]) -> List[str]:
        """Build the command to execute for a workflow type"""
        base_commands = {
            "main": ["python", "main.py"],
            "evaluate": ["python", "evaluate_projects.py"],
            "generate": ["python", "main.py", "--generate-applications"],
            "email_ingest": ["python", "main.py", "--email-ingest"],
            "rss_ingest": ["python", "main.py", "--rss-ingest"]
        }

        if workflow_type not in base_commands:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        command = base_commands[workflow_type].copy()

        # Add parameters based on workflow type
        if workflow_type == "main":
            if "number" in parameters:
                command.extend(["-n", str(parameters["number"])])
            if "regions" in parameters:
                if isinstance(parameters["regions"], list):
                    command.extend(["-r"] + parameters["regions"])
                else:
                    command.extend(["-r", parameters["regions"]])
            if "output_dir" in parameters:
                command.extend(["-o", parameters["output_dir"]])
            if parameters.get("no_applications"):
                command.append("--no-applications")
            if parameters.get("no_purge"):
                command.append("--no-purge")

        elif workflow_type == "evaluate":
            if parameters.get("pre_eval_only"):
                command.append("--pre-eval-only")

        elif workflow_type == "generate":
            if parameters.get("all_accepted"):
                command.append("--all-accepted")
            if "threshold" in parameters:
                command.extend(["--application-threshold", str(parameters["threshold"])])

        elif workflow_type in ("email_ingest", "rss_ingest"):
            # Required parameters
            if "provider" not in parameters:
                raise ValueError(f"Provider is required for {workflow_type}")
            command.extend(["--provider", parameters["provider"]])

            # Optional parameters
            if "output_dir" in parameters:
                command.extend(["-o", parameters["output_dir"]])
            if parameters.get("dry_run"):
                command.append("--dry-run")

        # Add any custom arguments
        if "custom_args" in parameters:
            if isinstance(parameters["custom_args"], list):
                command.extend(parameters["custom_args"])
            else:
                command.extend(parameters["custom_args"].split())

        logger.debug(f"Built command for {workflow_type}: {' '.join(command)}")
        return command

# Global instance
scheduler_manager = SchedulerManager()

def get_scheduler_manager() -> SchedulerManager:
    """Get the global scheduler manager instance"""
    return scheduler_manager