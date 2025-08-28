#!/usr/bin/env python3
"""
Background Application Processor
Monitors queue directory and processes application generation requests

This script implements a file-based queue system that maintains the static
nature of the dashboard while enabling seamless background processing.
"""

import json
import time
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from application_generator import create_application_generator, load_application_config

class ApplicationQueueProcessor:
    """
    Background processor for application generation requests.

    Monitors the application_queue directory for new requests, processes them
    using the existing ApplicationGenerator, and writes response files back
    to the queue for dashboard consumption.
    """

    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the Application Queue Processor.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = load_application_config(config_path)
        self.generator = create_application_generator(config_path)
        self.cv_content = self.load_cv_content()

        # Set up queue directory paths
        self.queue_dir = Path("application_queue")
        self.requests_dir = self.queue_dir / "requests"
        self.responses_dir = self.queue_dir / "responses"
        self.processing_dir = self.queue_dir / "processing"
        self.failed_dir = self.queue_dir / "failed"

        # Create directories if they don't exist
        self._ensure_directories()

        # Set up logging
        self._setup_logging()

        print("✅ Application Queue Processor initialized")
        print(f"   Queue directory: {self.queue_dir.absolute()}")
        print(f"   CV file loaded: {len(self.cv_content)} characters")

    def _ensure_directories(self) -> None:
        """Create queue directories if they don't exist."""
        for dir_path in [self.requests_dir, self.responses_dir,
                        self.processing_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self) -> None:
        """Set up logging for the processor."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('application_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_cv_content(self) -> str:
        """
        Load CV content from file.

        Returns:
            CV content as string

        Raises:
            FileNotFoundError: If CV file not found
        """
        cv_file = self.config.get('cv_file', 'cv.md')
        try:
            with open(cv_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"CV file not found: {cv_file}")

    def process_queue(self, once: bool = False) -> None:
        """
        Main processing loop.

        Args:
            once: If True, process once and exit. If False, run continuously.
        """
        self.logger.info("Starting application queue processor")
        print("🚀 Application Queue Processor started")
        print("   Monitoring for new requests...")

        while True:
            try:
                # Get list of request files
                request_files = list(self.requests_dir.glob("*.json"))

                if request_files:
                    self.logger.info(f"Found {len(request_files)} request(s) to process")
                    print(f"📋 Processing {len(request_files)} request(s)...")

                    for request_file in request_files:
                        try:
                            self.process_request(request_file)
                        except Exception as e:
                            self.logger.error(f"Error processing {request_file.name}: {e}")
                            print(f"❌ Error processing {request_file.name}: {e}")

                if once:
                    break

                # Wait before checking again
                time.sleep(2)

            except KeyboardInterrupt:
                self.logger.info("Processor stopped by user")
                print("\n🛑 Processor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                print(f"❌ Error in processing loop: {e}")
                time.sleep(5)  # Wait longer on errors

    def process_request(self, request_file: Path) -> None:
        """
        Process a single request file atomically.

        Args:
            request_file: Path to request file
        """
        request_id = request_file.stem
        self.logger.info(f"Processing request: {request_id}")

        # Move to processing directory (atomic operation)
        processing_file = self.processing_dir / request_file.name
        try:
            shutil.move(str(request_file), str(processing_file))
        except Exception as e:
            self.logger.error(f"Failed to move request to processing: {e}")
            return

        try:
            # Load and validate request
            with open(processing_file, 'r', encoding='utf-8') as f:
                request = json.load(f)

            # Create processing response
            self.create_response(request_id, 'processing', request)

            # Process application generation
            result = self.generate_application(request)

            # Create success response
            self.create_response(request_id, 'success', request, result)

            # Clean up processing file
            processing_file.unlink()

            self.logger.info(f"Successfully processed request: {request_id}")

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error processing request {request_id}: {error_msg}")

            # Create error response
            self.create_response(request_id, 'failed', request, error=error_msg)

            # Move to failed directory
            try:
                failed_file = self.failed_dir / processing_file.name
                shutil.move(str(processing_file), str(failed_file))
            except Exception as move_error:
                self.logger.error(f"Failed to move to failed directory: {move_error}")

    def generate_application(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate application using existing ApplicationGenerator.

        Args:
            request: Request data

        Returns:
            Processing result
        """
        project_file = request['project_file']
        project_id = request['project_id']

        self.logger.info(f"Generating application for project: {project_id}")
        print(f"🤖 Generating application for: {project_id}")

        # Use existing ApplicationGenerator with high fit score for manual generation
        result = self.generator.process_project(
            project_file, self.cv_content, fit_score=95
        )

        return result

    def create_response(self, request_id: str, status: str,
                       request: Dict[str, Any], result: Dict[str, Any] = None,
                       error: str = None) -> None:
        """
        Create response file for dashboard consumption.

        Args:
            request_id: Unique request identifier
            status: Response status (processing, success, failed)
            request: Original request data
            result: Processing result (for success responses)
            error: Error message (for failed responses)
        """
        response = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'project_id': request.get('project_id'),
            'result': result,
            'error': error
        }

        response_file = self.responses_dir / f"{request_id}.json"
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Created {status} response for request: {request_id}")

    def get_queue_status(self) -> Dict[str, int]:
        """
        Get current queue status.

        Returns:
            Dictionary with queue statistics
        """
        return {
            'requests': len(list(self.requests_dir.glob("*.json"))),
            'processing': len(list(self.processing_dir.glob("*.json"))),
            'responses': len(list(self.responses_dir.glob("*.json"))),
            'failed': len(list(self.failed_dir.glob("*.json")))
        }


def main():
    """Main entry point for command line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Background Application Processor for Bewerbungs-Bot"
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Process once and exit instead of running continuously"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current queue status and exit"
    )

    args = parser.parse_args()

    try:
        processor = ApplicationQueueProcessor(args.config)

        if args.status:
            # Show queue status
            status = processor.get_queue_status()
            print("📊 Queue Status:")
            print(f"   Requests: {status['requests']}")
            print(f"   Processing: {status['processing']}")
            print(f"   Responses: {status['responses']}")
            print(f"   Failed: {status['failed']}")
            return

        # Start processing
        processor.process_queue(once=args.once)

    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()