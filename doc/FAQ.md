# Frequently Asked Questions

## How do I install the dependencies?
Run `pip install -r requirements.txt` in your activated environment.

## How do I generate meeting minutes?
Use `scripts/transcript2json.py` to convert a transcript to JSON and then `scripts/json2word.py` to create DOCX or Markdown minutes.

## Where are the output files stored?
By default, minutes are written to `../MeetingSecretaryAI_Data/output`. You can change this in `config.ini` or via the GUI.
