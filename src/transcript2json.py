import argparse
import os
import configparser
import json
from datetime import date
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def load_file_content(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def load_system_prompt(prompt_file_path, context, agenda=""):
    """
    Loads the system prompt from an external file and formats it with the provided context.
    The external prompt may contain placeholders {context} and {agenda}, but agenda is optional.
    """
    prompt_template = load_file_content(prompt_file_path)
    return prompt_template.format(context=context, agenda=agenda)

def generate_summary(system_prompt, transcript_content, model, response_settings, json_schema, client):
    try:
        response_args = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"""
                        --- RAW TRANSCRIPT START ---
                        {transcript_content}
                        --- RAW TRANSCRIPT END ---
                        Please generate a structured output based on the schema provided.
                        """
                    )
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "minutes_structure",
                    "strict": True,
                    "schema": json_schema
                }
            }
        }

        if not (model.startswith("o1") or model.startswith("o3")):
            response_args.update({
                "temperature": response_settings['temperature'],
                "max_tokens": response_settings['max_tokens'],
                "top_p": response_settings['top_p'],
                "frequency_penalty": response_settings['frequency_penalty'],
                "presence_penalty": response_settings['presence_penalty']
            })

        response = client.chat.completions.create(**response_args)
        raw_output = response.choices[0].message.content.strip()
        structured_output = json.loads(raw_output)

        if structured_output is None:
            raise ValueError("Structured output is None")

        return structured_output

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return None
    except Exception as e:
        print(f"Error during processing: {e}")
        return None

def process_meeting_file(input_file_path, context_file_path, agenda_file_path, prompt_file_path,
                         output_file_path, model, response_settings, json_schema, client):
    # Load context, agenda (if provided), and system prompt
    context = load_file_content(context_file_path)
    agenda = load_file_content(agenda_file_path) if agenda_file_path else ""
    system_prompt = load_system_prompt(prompt_file_path, context, agenda)

    # Load transcript content
    transcript_content = load_file_content(input_file_path)

    structured_output = generate_summary(system_prompt, transcript_content, model, response_settings, json_schema, client)

    if structured_output:
        with open(output_file_path, 'w') as summary_file:
            summary_file.write(json.dumps(structured_output, indent=4))
        print(f"Structured output saved to {output_file_path}")
    else:
        print("Failed to generate structured output.")

def main():
    parser = argparse.ArgumentParser(description="Generate meeting minutes from a transcript using Azure OpenAI.")
    parser.add_argument("--input_file", required=True, help="Path to the meeting transcript file.")
    parser.add_argument("--context_file", required=True, help="Path to the context file.")
    parser.add_argument("--agenda_file", help="Path to the agenda file (optional).")
    parser.add_argument("--output_file", required=True, help="Path where the output file will be saved.")
    parser.add_argument("--prompt_file", default="scripts/prompt.md",
                        help="Path to the system prompt file (default: scripts/prompt.md).")
    parser.add_argument("--schema_file", default="scripts/minutes_schema.JSON",
                        help="Path to the JSON schema file (default: scripts/minutes_schema.JSON).")
    parser.add_argument("--config_file", default="config.ini",
                        help="Path to the configuration file (default: config.ini).")
    
    args = parser.parse_args()

    # Load configuration from the specified config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    # Extract response settings from the config file
    response_settings = {
        'temperature': config.getfloat('response_settings', 'temperature'),
        'max_tokens': config.getint('response_settings', 'max_tokens'),
        'top_p': config.getfloat('response_settings', 'top_p'),
        'frequency_penalty': config.getfloat('response_settings', 'frequency_penalty'),
        'presence_penalty': config.getfloat('response_settings', 'presence_penalty')
    }

    # Load the JSON schema for structured outputs
    with open(args.schema_file, 'r') as schema_file:
        json_schema = json.load(schema_file)

    # Extract the model name from environment variables
    model = os.environ['MODEL']
    print(f"Using model: {model}")

    # Initialize the Azure OpenAI client with the API key from environment variables
    client = AzureOpenAI(
        api_key=os.environ['OPENAI_API_KEY'],
        api_version=os.environ['API_VERSION'],
        azure_endpoint=os.environ['OPENAI_API_BASE'],
        organization=os.environ['OPENAI_ORGANIZATION']
    )

    process_meeting_file(
        input_file_path=args.input_file,
        context_file_path=args.context_file,
        agenda_file_path=args.agenda_file if args.agenda_file else None,
        prompt_file_path=args.prompt_file,
        output_file_path=args.output_file,
        model=model,
        response_settings=response_settings,
        json_schema=json_schema,
        client=client
    )

if __name__ == "__main__":
    main()
