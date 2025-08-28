import os
import yaml
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from openai import OpenAI, RateLimitError, AuthenticationError
from anthropic import Anthropic, APIStatusError as AnthropicAPIStatusError
import google.generativeai as genai

LOG_DIR = 'projects_log'
Path(LOG_DIR).mkdir(exist_ok=True)

def setup_logging(log_file_name):
    """Sets up a log file for a specific project evaluation."""
    log_path = os.path.join(LOG_DIR, log_file_name)
    def log_message(message):
        """Writes a timestamped message to the log file."""
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    return log_message

def load_config(config_path):
    """
    Loads the configuration from the specified YAML file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The loaded configuration.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        # Set default threshold if not provided
        if 'settings' not in config or 'acceptance_threshold' not in config['settings']:
            config.setdefault('settings', {})['acceptance_threshold'] = 85
            print("Info: 'acceptance_threshold' not found in config, defaulting to 85%.")
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_path}'")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None

def parse_cv(cv_path):
    """
    Parses the CV file and returns its content.

    Args:
        cv_path (str): The path to the CV file.

    Returns:
        str: The content of the CV.
    """
    try:
        with open(cv_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: CV file not found at '{cv_path}'")
        return None

def parse_input_file(file_path):
    """
    Parses a single project offer file (email or Markdown).

    Args:
        file_path (str): The path to the input file.

    Returns:
        str: The cleaned content of the file, or None if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # For Markdown, no specific cleaning is applied for now
        # Future enhancements could go here
        
        return content.strip()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def pre_evaluate_project(project_content, config, log):
    """
    Performs a pre-evaluation of the project based on keywords.

    Args:
        project_content (str): The content of the project offer.
        config (dict): The pre-evaluation configuration.
        log (function): The logging function to use.

    Returns:
        tuple: A tuple containing the fit score (int) and a rationale (str).
    """
    pre_eval_config = config.get('pre_evaluation', {})
    if not pre_eval_config:
        return 100, "No pre-evaluation rules configured. Skipping."

    content_lower = project_content.lower()
    
    # 1. Check for forbidden tags
    forbidden_tags = pre_eval_config.get('forbidden_tags', [])
    if isinstance(forbidden_tags, list):
        for tag in forbidden_tags:
            # Use word boundaries to avoid partial matches (e.g., 'java' in 'javascript')
            if re.search(r'\b' + re.escape(tag.lower()) + r'\b', content_lower):
                rationale = f"Rejected: Contains forbidden tag '{tag}'."
                log(rationale) # Add specific logging for diagnosis
                return -1, rationale
    
    # 2. Check for required tags
    required_tags = pre_eval_config.get('required_tags', [])
    for tag in required_tags:
        if tag.lower() not in content_lower:
            return 0, f"Rejected: Missing required tag '{tag}'."

    # 3. Calculate weighted score
    weighted_tags = pre_eval_config.get('weighted_tags', {})
    if not weighted_tags:
        # If no weighted tags, and it passed forbidden/required checks, it's a pass.
        return 100, "Passed: No weighted tags to score against."

    total_score = 0
    max_score = sum(weighted_tags.values())
    
    found_tags = []
    for tag, weight in weighted_tags.items():
        if tag.lower() in content_lower:
            total_score += weight
            found_tags.append(tag)

    if max_score == 0:
        return 100, "Passed: No weighted tags configured."

    fit_score = int((total_score / max_score) * 100)
    rationale = f"Score: {fit_score}%. Found tags: {found_tags}"
    
    return fit_score, rationale


def analyze_with_llm(cv_content, project_offer, config):
    """
    Analyzes the project offer against the CV using the configured LLM.

    Args:
        cv_content (str): The content of the CV.
        project_offer (str): The content of the project offer.
        config (dict): The configuration dictionary.

    Returns:
        dict: A dictionary with 'fit_score' and 'rationale'.
    """
    provider = config.get('llm', {}).get('provider')
    model = config.get('llm', {}).get('model')
    api_key = config.get('llm', {}).get('api_key')

    if not all([provider, model, api_key]):
        return {"fit_score": 0, "rationale": "Error: LLM provider, model, or API key is missing from the configuration."}

    prompt = f"""
    As an expert technical recruiter, please analyze the following project offer and CV.

    CV:
    ---
    {cv_content}
    ---

    Project Offer:
    ---
    {project_offer}
    ---

    Your task is to:
    1.  Identify the key requirements from the project offer (skills, technologies, experience).
    2.  Compare these requirements against the CV.
    3.  Provide a concise rationale for your assessment in a markdown list.
    4.  Calculate a "fit score" from 0 to 100.
    5.  Return the output as a JSON object with the structure: {{"fit_score": <integer>, "rationale": "<string>"}}
    """

    try:
        if provider == 'OpenAI':
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)

        elif provider == 'Anthropic':
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model, max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            json_str = re.search(r'{.*}', response.content[0].text, re.DOTALL)
            if json_str:
                return json.loads(json_str.group(0))
            else:
                return {"fit_score": 0, "rationale": "Error: Could not parse JSON from Anthropic response."}

        elif provider == 'Google':
            genai.configure(api_key=api_key)
            genai_model = genai.GenerativeModel(model)
            response = genai_model.generate_content(prompt)
            # Clean up the response to extract only the JSON part
            text_response = response.text.strip()
            json_str_match = re.search(r'```json\s*(\{.*?\})\s*```', text_response, re.DOTALL)
            if json_str_match:
                json_str = json_str_match.group(1)
            else:
                json_str = text_response

            if json_str:
                return json.loads(json_str)
            else:
                return {"fit_score": 0, "rationale": "Error: Could not parse JSON from Google Gemini response."}

        else:
            return {"fit_score": 0, "rationale": f"Error: Unsupported LLM provider '{provider}'."}

    except AuthenticationError:
        return {"fit_score": 0, "rationale": f"Error: {provider} API key is invalid. Please check your config.yaml."}
    except RateLimitError:
        return {"fit_score": 0, "rationale": f"Error: Rate limit exceeded for {provider} API. Please try again later."}
    except AnthropicAPIStatusError as e:
        return {"fit_score": 0, "rationale": f"Error: Anthropic API request failed with status {e.status_code}: {e.response}"}
    except Exception as e:
        # Catch other google-specific API errors if possible, or a general one
        if "API key not valid" in str(e):
             return {"fit_score": 0, "rationale": "Error: Google Gemini API key is invalid. Please check your config.yaml."}
        return {"fit_score": 0, "rationale": f"An unexpected error occurred with {provider}: {e}"}


def process_project_file(project_path, config, cv_content, log_func=None):
    """
    Processes a single project file: logs, analyzes, and moves it.
    If a log_func is not provided, it sets one up.
    """
    project_filename = os.path.basename(project_path)
    # Use the passed logger or set up a new one
    if log_func is None:
        log_filename = f"{os.path.splitext(project_filename)[0]}.log"
        log = setup_logging(log_filename)
    else:
        log = log_func
    log("="*50)
    log(f"Starting evaluation for: {project_filename}")


    # Parse Project File
    log(f"Parsing project file: {project_path}")
    project_content = parse_input_file(project_path)
    if not project_content:
        log("Fatal: Could not parse project file. Aborting this file.")
        return

    # Pre-evaluation
    pre_eval_score, pre_eval_rationale = pre_evaluate_project(project_content, config, log)
    pre_eval_threshold = config.get('pre_evaluation', {}).get('acceptance_threshold', 50)
    log(f"Pre-evaluation score: {pre_eval_score}% (Threshold: {pre_eval_threshold}%)")
    log(f"Pre-evaluation rationale: {pre_eval_rationale}")

    # Decide action based on pre-evaluation score
    passed_pre_eval = pre_eval_score >= pre_eval_threshold
    dest_folder = 'projects_accepted' if passed_pre_eval else 'projects_rejected'
    
    # If in pre-eval-only mode, move the file and stop.
    if config.get('pre_eval_only', False):
        log(f"Result: Pre-evaluation only mode. Score: {pre_eval_score}%.")
        Path(dest_folder).mkdir(exist_ok=True)
        destination_path = os.path.join(dest_folder, project_filename)
        try:
            shutil.move(project_path, destination_path)
            log(f"File moved to '{destination_path}'.")
            print(f"-> Processed {project_filename} | Pre-eval Score: {pre_eval_score:<3}% | Moved to '{dest_folder}'")
        except Exception as e:
            error_msg = f"Fatal: Error moving file: {e}"
            log(error_msg)
            print(error_msg)
        log("Evaluation finished.")
        log("="*50 + "\n")
        return
        
    # If not passed, reject and stop
    if not passed_pre_eval:
        log("Result: Rejected based on pre-evaluation.")
        Path(dest_folder).mkdir(exist_ok=True)
        destination_path = os.path.join(dest_folder, project_filename)
        try:
            shutil.move(project_path, destination_path)
            log(f"File moved to '{destination_path}'.")
            print(f"-> Processed {project_filename} | Pre-eval Score: {pre_eval_score:<3}% | Moved to '{dest_folder}'")
        except Exception as e:
            error_msg = f"Fatal: Error moving file: {e}"
            log(error_msg)
            print(error_msg)
        log("Evaluation finished.")
        log("="*50 + "\n")
        return

    log("Result: Passed pre-evaluation. Proceeding to LLM analysis.")

    # Get LLM acceptance threshold from config
    acceptance_threshold = config.get('settings', {}).get('acceptance_threshold', 85)
    log(f"Using LLM acceptance threshold of {acceptance_threshold}%.")

    # Analyze with LLM
    log("Sending data to LLM for analysis...")
    analysis = analyze_with_llm(cv_content, project_content, config)
    fit_score = analysis.get('fit_score', 0)
    rationale = analysis.get('rationale', 'No rationale provided.')
    log(f"LLM analysis complete. Fit Score: {fit_score}%.")

    # Handle rationale if it's a list
    if isinstance(rationale, list):
        rationale_text = "\n".join(f"- {item}" for item in rationale)
    else:
        rationale_text = str(rationale).strip()

    log(f"Rationale:\n{rationale_text}")

    # Decision and File Move
    dest_folder = 'projects_accepted' if fit_score >= acceptance_threshold else 'projects_rejected'
    Path(dest_folder).mkdir(exist_ok=True)
    destination_path = os.path.join(dest_folder, project_filename)

    try:
        shutil.move(project_path, destination_path)
        log(f"File moved to '{destination_path}'.")
        print(f"-> Processed {project_filename} | Score: {fit_score:>3}% | Moved to '{dest_folder}'")
    except Exception as e:
        error_msg = f"Fatal: Error moving file: {e}"
        log(error_msg)
        print(error_msg)
    log("Evaluation finished.")
    log("="*50 + "\n")

def main():
    """Main function to run the project evaluation script."""
    parser = argparse.ArgumentParser(
        description="Evaluate project offers against a CV. Processes a single file or all files in the projects directory.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  # Process all projects in the default 'projects' directory
  python evaluate_projects.py

  # Process a single specific project
  python evaluate_projects.py projects/project_offer_01.md

  # Process all projects using a custom config file
  python evaluate_projects.py --config custom_config.yaml
"""
    )
    parser.add_argument('project_file', nargs='?', default=None, help='Optional: Path to a specific project file to process.')
    parser.add_argument('--config', default='config.yaml', help='Path to the configuration file (default: config.yaml)')
    parser.add_argument('--cv', default='cv.md', help='Path to the CV file (default: cv.md)')
    parser.add_argument('--projects-dir', default='projects', help="Directory containing projects to process (default: 'projects')")
    parser.add_argument('--pre-eval-only', action='store_true', help='Run only the pre-evaluation scoring without calling the LLM.')
    args = parser.parse_args()

    # --- Common Setup ---
    config = load_config(args.config)
    if not config:
        print("Fatal: Could not load configuration. Exiting.")
        return

    # Add the pre_eval_only flag to the config dictionary for easy access
    config['pre_eval_only'] = args.pre_eval_only
    if args.pre_eval_only:
        print("--- Running in PRE-EVALUATION ONLY mode ---")


    cv_content = parse_cv(args.cv)
    if not cv_content:
        print("Fatal: Could not load CV. Exiting.")
        return

    # --- Main Logic ---
    if args.project_file:
        # Process a single file
        print(f"Processing single file: {args.project_file}")
        if not os.path.exists(args.project_file):
            print(f"Error: Specified project file not found at '{args.project_file}'")
            return
        process_project_file(args.project_file, config, cv_content)
    else:
        # Process all files in the directory
        print(f"Processing all projects in '{args.projects_dir}' directory...")
        if not os.path.isdir(args.projects_dir):
            print(f"Error: Projects directory not found at '{args.projects_dir}'")
            return
        
        project_files = [os.path.join(args.projects_dir, f) for f in os.listdir(args.projects_dir) if f.endswith(('.txt', '.eml', '.md'))]
        
        if not project_files:
            print("No project files found to process.")
            return

        # Create a single logger for the batch run
        batch_log_filename = f"batch_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log = setup_logging(batch_log_filename)
        print(f"Processing all projects. See log file for details: {os.path.join(LOG_DIR, batch_log_filename)}")

        for project_path in project_files:
            process_project_file(project_path, config, cv_content, log)
        
        print("\nAll projects processed.")

if __name__ == "__main__":
    main()