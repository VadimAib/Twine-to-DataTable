# Twine to Unreal Engine Parser

A Python-based pipeline to convert a Twine (`.twee`) story into a JSON file, ready for import as a DataTable in Unreal Engine.

## Features

- **Metadata Extraction:** Automatically extracts Title, IFID, Format, and Start Node from `StoryData`.
- **Advanced Parsing:** Supports conditional text (`<<if>>`), inline actions (`[$var = value]`), and rich text formatting (Markdown to UE Rich Text).
- **Strict Validation:** Automatically stops on broken links, duplicate nodes, missing start node, or unsupported nested conditions.
- **Smart Execution:** Skips the pipeline if the input file hasn't changed since the last run.
- **Safety:** Automated numbered backups (only when files actually change) and detailed timestamped logging.
- **Zero Configuration:** Automatically detects input files and generates output names.

## Requirements

- Python 3.8 or higher
- Windows OS (for `build_dialogue.bat`) or any OS with a compatible shell script

## Installation

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Clone or download this repository
3. Place your `.twee` file in the project root directory

## Usage

### Auto-detect single file

If there is only one `.twee` file in the directory:

```bash
build_dialogue.bat
```

### Specify input file

If there are multiple files, or you want to be explicit:

```bash
build_dialogue.bat "MyStory.twee"
```

### Example output

```
============================================================
Twine to DataTable Conversion Pipeline
============================================================

Input file: "MyStory.twee"

[12:00:00] INFO: Twine → Unreal Engine Conversion Pipeline
[12:00:00] INFO: Output file: MyStory.json
[12:00:00] INFO: Run number: 1

[12:00:00] [Stage 1/6] Checking for backups...
[12:00:00] [Stage 2/6] Normalizing encoding
[12:00:00] [Stage 3/6] Parsing Twee
[12:00:00] [Stage 4/6] Validating
[12:00:00] [Stage 5/6] Transforming
[12:00:00] [Stage 6/6] Generating report

[12:00:01] OK: Pipeline completed successfully!

Log saved: logs\pipeline.1.log
```

### Re-running without changes

If the input `.twee` file hasn't been modified since the last run, the pipeline will skip automatically:

```
[INFO] No changes detected in: MyStory.twee
[INFO] Pipeline skipped. Output is up to date.
```

## Output

The pipeline generates a JSON file named `<InputFileName>.json` (e.g., `MyStory.json`). This file is structured specifically for Unreal Engine Data Tables and can be imported directly via the Content Browser.

## Validation

The pipeline performs strict validation and will **stop** if it finds:

- Duplicate node IDs
- Missing start node (as defined in `StoryData.start`)
- Broken links (references to non-existent nodes)
- Nested `<<if>>` conditions (not supported)

Fix any reported errors in your `.twee` file and run the pipeline again.

## Logs and Backups

### Logs

Each successful run creates numbered files in the `logs/` directory:

- `pipeline.N.log` — detailed technical log with timestamps
- `report.N.txt` — human-readable report with statistics and variables
- `variables.N.json` — machine-readable variable data for comparison

Where `N` is the run number (1, 2, 3, ...).

### Backups

Before overwriting the output JSON, the pipeline creates a numbered backup in the `backups/` directory:

- `<OutputFile>.1.backup`
- `<OutputFile>.2.backup`

Backups are only created when the file actually changes.

## Project Structure

```text
├── scripts/                 # Python pipeline scripts
│   ├── logger.py            # Centralized logging system
│   ├── 00_backup.py         # Automated backup handler
│   ├── 01_normalize_encoding.py
│   ├── 02_parse_twee.py
│   ├── 03_validate.py
│   ├── 04_transform.py
│   ├── 05_report.py
│   └── run_pipeline.py      # Main orchestrator
├── temp/                    # Intermediate files (gitignored)
├── logs/                    # Logs and reports (gitignored)
├── backups/                 # Versioned backups (gitignored)
├── build_dialogue.bat       # Entry point
├── README.md
└── LICENSE
```

## Twee File Requirements

- **Format:** SugarCube 2.x
- **Mandatory Passages:**
  - `:: StoryTitle` — project title
  - `:: StoryData` — metadata (IFID, format, start node)
- **Start Node:** Defined in `StoryData.start` (defaults to `Start` if omitted)

### Example StoryData

```json
:: StoryData
{
  "ifid": "BEFE126C-35D2-4115-86E3-567EE32162EE",
  "format": "SugarCube",
  "format-version": "2.37.3",
  "start": "Start"
}
```

## Supported Syntax

### Links

```
[[Text|NodeName]]
[[Text->NodeName]]
[[NodeName<-Text]]
```

### Inline Actions

```
[[Text|NodeName][$var = value]]
[[Text|NodeName][$var += 1]]
```

### Conditions

```
<<if $var >= 5>>
  [[Conditional Choice|NodeName]]
<<endif>>
```

### Rich Text Formatting

| Markdown | UE Rich Text |
|----------|--------------|
| `**bold**` or `__bold__` | `<b>bold</>` |
| `*italic*` or `_italic_` | `<i>italic</>` |
| `~~strikethrough~~` | `<s>strikethrough</>` |

## Unreal Engine Integration

### Importing JSON into Unreal Engine

1. Open your UE project
2. In Content Browser, right-click → **Import to /Game/...**
3. Select the generated `.json` file
4. In the import dialog, set:
   - **Import Type:** DataTable
   - **Row Structure:** Create a new struct (see below)
   - **Import Key Field:** `RowName`
5. Click **Import**

The `RowName` field in the JSON is used as the DataTable row key. Each node's `NodeID` from the `.twee` file becomes the row name in the DataTable.

### Required Structs

Create the following Blueprint Structs in your UE project:

#### 1. ConditionStruct

Represents a condition for displaying text or choices.

| Field | Type | Description |
|-------|------|-------------|
| Type | String | Condition type: `Always`, `Bool`, `NotBool`, `Comparison` |
| VariableName | String | Name of the variable to check |
| Operator | String | Comparison operator: `>=`, `<=`, `==`, `!=`, `>`, `<` (empty for boolean checks) |
| Value | String | Value to compare against (empty for boolean checks) |

#### 2. DialogueActionStruct

Represents an action to modify a variable.

| Field | Type | Description |
|-------|------|-------------|
| VariableName | String | Name of the variable to modify |
| Operation | String | Operation type: `SET_Int`, `SET_Bool`, `SET_Float`, `ADD_Int`, `SUB_Int`, `UNSET` |
| Value | String | Value to set/add/subtract |

#### 3. TextSegmentStruct

Represents a text segment with an optional condition.

| Field | Type | Description |
|-------|------|-------------|
| Text | String | Dialogue text (supports UE Rich Text tags) |
| ConditionID | ConditionStruct | Condition for displaying this text |

#### 4. DialogueChoiceStruct

Represents a player choice with optional conditions and actions.

| Field | Type | Description |
|-------|------|-------------|
| ChoiceText | String | Text displayed to the player |
| NextNodeID | String | ID of the next node to navigate to |
| ConditionID | ConditionStruct | Condition for showing this choice |
| AutoTransition | Boolean | If true, automatically transition to NextNodeID without player input |
| InlineActions | Array of DialogueActionStruct | Actions to execute when this choice is selected |
| InlineText | String | Additional text to display (currently unused) |

#### 5. DialogueNodeStruct

The main struct for each row in the DataTable.

| Field | Type | Description |
|-------|------|-------------|
| RowName | String | Unique identifier for this node (automatically set by DataTable from Import Key Field) |
| TextSegments | Array of TextSegmentStruct | Text to display (can have multiple segments with different conditions) |
| Actions | Array of DialogueActionStruct | Actions to execute when entering this node |
| Choices | Array of DialogueChoiceStruct | Available choices for the player |

### Blueprint Logic Overview

To implement a dialogue system in Blueprints, you need to:

1. **Load the DataTable** at game start
2. **Find the current node** by RowName
3. **Evaluate conditions** for each TextSegment and Choice
4. **Display text** that passes conditions
5. **Show choices** that pass conditions
6. **Execute actions** when entering a node or selecting a choice
7. **Navigate** to the next node when a choice is selected

### Handling Conditions

The `Type` field in `ConditionStruct` determines how to evaluate the condition:

- **Always** — condition is always true, display the text/choice
- **Bool** — check if the boolean variable is true
- **NotBool** — check if the boolean variable is false
- **Comparison** — compare the variable value using the operator

Example evaluation logic:

```
if Condition.Type == "Always":
    return true
elif Condition.Type == "Bool":
    return GetVariable(Condition.VariableName) == true
elif Condition.Type == "NotBool":
    return GetVariable(Condition.VariableName) == false
elif Condition.Type == "Comparison":
    var_value = GetVariable(Condition.VariableName)
    compare_value = float(Condition.Value)
    
    if Condition.Operator == ">=":
        return var_value >= compare_value
    elif Condition.Operator == "<=":
        return var_value <= compare_value
    elif Condition.Operator == "==":
        return var_value == compare_value
    elif Condition.Operator == "!=":
        return var_value != compare_value
    elif Condition.Operator == ">":
        return var_value > compare_value
    elif Condition.Operator == "<":
        return var_value < compare_value
```

### Handling Actions

The `Operation` field in `DialogueActionStruct` determines how to modify the variable:

- **SET_Int**, **SET_Bool**, **SET_Float** — set variable to the specified value
- **ADD_Int**, **ADD_Bool**, **ADD_Float** — add the value to the variable
- **SUB_Int**, **SUB_Bool**, **SUB_Float** — subtract the value from the variable
- **UNSET** — unset/clear the variable

Example execution logic:

```
if Action.Operation == "SET_Int":
    SetVariable(Action.VariableName, int(Action.Value))
elif Action.Operation == "ADD_Int":
    current_value = GetVariable(Action.VariableName)
    SetVariable(Action.VariableName, current_value + int(Action.Value))
elif Action.Operation == "SUB_Int":
    current_value = GetVariable(Action.VariableName)
    SetVariable(Action.VariableName, current_value - int(Action.Value))
elif Action.Operation == "SET_Bool":
    SetVariable(Action.VariableName, Action.Value == "true")
elif Action.Operation == "UNSET":
    ClearVariable(Action.VariableName)
```

### AutoTransition

When a node has only one choice and `AutoTransition` is `true`, the dialogue system should automatically navigate to the next node without waiting for player input.

Example logic:

```
if Node.Choices.length == 1 and Node.Choices[0].AutoTransition == true:
    NavigateToNode(Node.Choices[0].NextNodeID)
else:
    DisplayChoices(Node.Choices)
    Wait for player selection
```

### Rich Text Support

The parser converts Markdown formatting to Unreal Engine Rich Text tags:

- `**bold**` or `__bold__` → `<b>bold</>`
- `*italic*` or `_italic_` → `<i>italic</>`
- `~~strikethrough~~` → `<s>strikethrough</>`

To display Rich Text in UE:

1. Use a **Text Render Component** or **Text Block** widget
2. Set the text using the `Text` field from `TextSegmentStruct`
3. Enable **Rich Text** in the widget properties
4. The UE Rich Text system will automatically parse and render the tags

Example:

```
Text: "<i>The path to the coast begins.</>"

Result: Italic text "The path to the coast begins."
```

## Disclaimer

This code was generated almost entirely using **Qwen3.7-Plus**. I created it for my own purposes and did not invest time in polishing it for public release. However, I decided to share it on the off chance that it saves someone else a few hours of work. Please treat it as a community contribution, not a production-grade solution.