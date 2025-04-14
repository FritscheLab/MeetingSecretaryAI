# Meeting Secretary AI 2.0 - Project Summary

## Project Purpose

Meeting Secretary AI automates the process of transforming raw meeting transcripts into structured, professional meeting minutes. It saves time for teams by eliminating the need for manual note-taking and formatting, while offering flexible output customization.

## Technical Architecture

The system uses a three-stage pipeline architecture:

1. **Extraction Stage** (`extract_agenda_items.py`):
   - Parses raw transcript files with timestamps
   - Uses Azure OpenAI to identify separate agenda items
   - Creates individual text files for each agenda item
   - Preserves original timestamps for reference

2. **JSON Transformation Stage** (`transcript2json.py`):
   - Processes each agenda item using selected prompt style
   - Uses Azure OpenAI to generate structured JSON output
   - Identifies discussion points, decisions, action items
   - Creates detailed JSON that follows the minutes schema

3. **Document Generation Stage** (`json2word.py`):
   - Transforms JSON content into formatted documents
   - Offers both DOCX and Markdown output formats
   - Creates professional formatting with styles
   - Includes consolidated action items and references

## Key Features

- **Multiple Prompt Styles**: Choose from concise, moderate, high detail, in-person, or subjective styles
- **Output Format Options**: Generate Word documents, Markdown files, or both
- **Multi-transcript Support**: Process meetings split across multiple files
- **Title Preservation**: Maintain original agenda item titles throughout the pipeline
- **Timestamp Analysis**: Use timestamps to identify when topics were discussed
- **Gap Detection and Merging**: Configure thresholds for merging agenda items
- **Structured Output**: Generate consistently formatted documents
- **Customizable Content**: Control which sections appear in the final document
- **Next Meeting Information**: Include details about upcoming meetings
- **Reference Tracking**: Comprehensive tracking of documents, URLs, and other resources mentioned
- **Configurable Similarity Matching**: Adjust thresholds for agenda title matching

## Data Flow

```
Raw Transcripts → Agenda Items → Segment JSONs → Consolidated JSON → DOCX/MD Output
```

## Prompt Styles

The system offers five different prompt styles to meet different meeting documentation needs:

1. **Concise**: Minimal detail, focused on high-level takeaways and key decisions
2. **Moderate**: Balanced detail level for standard meeting documentation
3. **High**: Maximum detail including comprehensive discussion records
4. **High In-Person**: Maximum detail without speaker attribution (for meetings with unreliable speaker identification)
5. **High Subjective**: Exhaustive, richly narrative minutes that preserve every detail while organizing content by discussion subtopics, with expanded rationale and reference tracking

## Extensibility

The system can be extended by:
- Adding more prompt styles for different use cases
- Creating additional output formats beyond DOCX and Markdown
- Integrating with meeting recording platforms
- Adding collaborative editing capabilities

## Future Improvements

- Enhanced participant identification and speaker tracking
- Support for additional languages beyond English
- Integration with project management tools (Jira, Asana, etc.)
- Web interface for managing the pipeline
- Real-time processing during live meetings
- Meeting analytics and insights dashboard
- Advanced sentiment analysis for discussion dynamics
- Automatic comparison with previous meeting minutes
- Support for additional output formats (PDF, HTML, etc.)
- Integration with calendar systems for meeting scheduling
- Automated follow-up reminders for action items