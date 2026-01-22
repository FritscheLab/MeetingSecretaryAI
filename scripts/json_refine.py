import argparse
import configparser
import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


def load_file_content(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def load_system_prompt(prompt_file_path):
    return load_file_content(prompt_file_path)


def refine_minutes(system_prompt, minutes_payload, model, response_settings, json_schema, client,
                   reasoning_effort):
    try:
        response_args = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "--- INPUT MINUTES JSON START ---\n"
                        f"{json.dumps(minutes_payload, indent=2)}\n"
                        "--- INPUT MINUTES JSON END ---\n"
                        "Please return improved minutes JSON that follows the provided schema."
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "minutes_structure",
                    "strict": True,
                    "schema": json_schema,
                },
            },
        }

        if reasoning_effort:
            response_args["reasoning_effort"] = reasoning_effort

        if not (
            model.startswith("o1")
            or model.startswith("o3")
            or model.startswith("o4")
            or model.startswith("gpt-5")
        ):
            response_args.update({
                "temperature": response_settings['temperature'],
                "max_tokens": response_settings['max_tokens'],
                "top_p": response_settings['top_p'],
                "frequency_penalty": response_settings['frequency_penalty'],
                "presence_penalty": response_settings['presence_penalty'],
            })

        if model.startswith("o4") or model.startswith("gpt-5"):
            response_args.update({
                "max_completion_tokens": response_settings['max_completion_tokens'],
            })

        response = client.chat.completions.create(**response_args)
        raw_output = response.choices[0].message.content.strip()
        structured_output = json.loads(raw_output)

        if structured_output is None:
            raise ValueError("Structured output is None")

        return structured_output

    except json.JSONDecodeError as exc:
        print(f"Failed to decode JSON: {exc}")
        return None
    except Exception as exc:
        print(f"Error during processing: {exc}")
        return None


def process_minutes_file(input_file_path, output_file_path, prompt_file_path,
                          model, response_settings, json_schema, client, reasoning_effort):
    system_prompt = load_system_prompt(prompt_file_path)

    with open(input_file_path, 'r') as minutes_file:
        minutes_payload = json.load(minutes_file)

    refined_output = refine_minutes(
        system_prompt,
        minutes_payload,
        model,
        response_settings,
        json_schema,
        client,
        reasoning_effort,
    )

    if refined_output:
        with open(output_file_path, 'w') as summary_file:
            summary_file.write(json.dumps(refined_output, indent=4))
        print(f"Refined minutes saved to {output_file_path}")
    else:
        print("Failed to refine minutes output.")


def main():
    parser = argparse.ArgumentParser(
        description="Refine meeting minutes JSON to reduce verbosity and redundancy."
    )
    parser.add_argument("--input_json", required=True, help="Path to the JSON minutes file.")
    parser.add_argument("--output_json", required=True, help="Path where the refined JSON will be saved.")
    parser.add_argument(
        "--prompt_file",
        default="scripts/prompt_refine.md",
        help="Path to the refinement system prompt file (default: scripts/prompt_refine.md).",
    )
    parser.add_argument(
        "--schema_file",
        default="scripts/minutes_schema.JSON",
        help="Path to the JSON schema file (default: scripts/minutes_schema.JSON).",
    )
    parser.add_argument(
        "--config_file",
        default="config.ini",
        help="Path to the configuration file (default: config.ini).",
    )

    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config_file)

    response_settings = {
        'temperature': config.getfloat('response_settings', 'temperature'),
        'max_tokens': config.getint('response_settings', 'max_tokens'),
        'max_completion_tokens': config.getint('response_settings', 'max_completion_tokens'),
        'top_p': config.getfloat('response_settings', 'top_p'),
        'frequency_penalty': config.getfloat('response_settings', 'frequency_penalty'),
        'presence_penalty': config.getfloat('response_settings', 'presence_penalty'),
    }

    with open(args.schema_file, 'r') as schema_file:
        json_schema = json.load(schema_file)

    model = os.environ.get('REFINEMENT_MODEL', os.environ['MODEL'])
    print(f"Using refinement model: {model}")

    client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_API_KEY'],
        api_version=os.environ['API_VERSION'],
        azure_endpoint=os.environ['OPENAI_API_BASE'],
        organization=os.environ['OPENAI_ORGANIZATION'],
    )

    reasoning_effort = config.get('response_settings', 'reasoning_effort_refine', fallback='').strip()

    process_minutes_file(
        input_file_path=args.input_json,
        output_file_path=args.output_json,
        prompt_file_path=args.prompt_file,
        model=model,
        response_settings=response_settings,
        json_schema=json_schema,
        client=client,
        reasoning_effort=reasoning_effort,
    )


if __name__ == "__main__":
    main()
