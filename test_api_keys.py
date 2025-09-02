import openai
import anthropic
import os
import argparse

def test_openai_key(api_key):
    """Test OpenAI API key by listing models."""
    openai.api_key = api_key
    try:
        models = openai.models.list()
        print("OpenAI API key is valid and working.")
        print("Available models:")
        for model in models.data:
            print(f"- {model.id}")
        return True
    except openai.AuthenticationError as e:
        print(f"OpenAI Authentication failed: {e}")
        print("The API key is invalid, expired, or has insufficient permissions.")
        return False
    except openai.RateLimitError as e:
        print(f"OpenAI Rate limit exceeded: {e}")
        print("The API key may be valid but has hit usage limits.")
        return False
    except Exception as e:
        print(f"OpenAI error: {e}")
        print("Unable to verify the API key due to an unexpected error.")
        return False

def test_anthropic_key(api_key):
    """Test Anthropic API key by listing models."""
    client = anthropic.Anthropic(api_key=api_key)
    try:
        models = client.models.list()
        print("Anthropic API key is valid and working.")
        print("Available models:")
        for model in models.data:
            print(f"- {model.id}")
        return True
    except Exception as e:
        print(f"Anthropic error: {e}")
        print("The API key is invalid, expired, or has insufficient permissions.")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="A utility script to validate API keys for OpenAI and Anthropic services by testing their ability to list available models.",
        epilog="""Environment Variables:
  OPENAI_API_KEY: Your OpenAI API key (required for OpenAI testing)
  ANTHROPIC_API_KEY: Your Anthropic API key (required for Anthropic testing)

Examples:
  export OPENAI_API_KEY='your-openai-key'
  python test_api_keys.py

  export ANTHROPIC_API_KEY='your-anthropic-key'
  python test_api_keys.py

  export OPENAI_API_KEY='your-openai-key' ANTHROPIC_API_KEY='your-anthropic-key'
  python test_api_keys.py

Note: At least one API key must be set. The script will test whichever keys are provided."""
    )
    parser.parse_args()  # This handles --help automatically

    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    if not openai_key and not anthropic_key:
        print("Error: Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY environment variables are set.")
        print("Please set at least one of them and run the script again.")
        print("Use --help for more information.")
        return

    if openai_key:
        print("Testing OpenAI API key...")
        test_openai_key(openai_key)
        print()
    else:
        print("OPENAI_API_KEY not set, skipping OpenAI test.\n")

    if anthropic_key:
        print("Testing Anthropic API key...")
        test_anthropic_key(anthropic_key)
        print()
    else:
        print("ANTHROPIC_API_KEY not set, skipping Anthropic test.\n")

if __name__ == "__main__":
    main()