# Workflow Diagram

```
Transcript -> transcript2json.py -> JSON -> json_refine.py -> JSON -> json2word.py -> DOCX
          \                                                          |
           \-> meeting_utils.py -------------------------------------/
```

This diagram shows the flow from raw transcript to final minutes using the main scripts.
