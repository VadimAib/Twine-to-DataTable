#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_transform.py
Transform intermediate JSON to final DataTable format
"""

import sys
import os
import json
import re
from logger import log_info, log_success, log_error, log_warning

def transform(input_file, output_file):
    """Transform intermediate JSON to final format"""
    
    log_info(f"Reading: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    
    final_nodes = []
    
    for node in nodes:
        if node['NodeID'] in ['StoryTitle', 'StoryData', ':: StoryTitle', ':: StoryData']:
            continue
        
        final_node = transform_node(node)
        final_nodes.append(final_node)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_nodes, f, ensure_ascii=False, indent=2)
    
    log_success(f"Transformed {len(final_nodes)} nodes")
    log_info(f"Output: {output_file}")

def transform_node(node):
    """Transform single node"""
    
    text = node['Text']
    
    # 1. Extract Actions
    actions = extract_actions(text)
    
    # 2. Process <<if>> → extract choices WITH conditions
    choices_from_if = []
    text_segments, text = process_if_conditions(text, choices_from_if)
    
    # 3. Extract remaining choices (not in if blocks)
    remaining_choices = extract_choices(text)
    
    # 4. Combine choices (if-choices first, then remaining)
    all_choices = choices_from_if + remaining_choices
    
    # 5. Remove links from text
    text = re.sub(r'\[\[.*?\]\]', '', text)
    
    # 6. Remove all macros
    text = re.sub(r'<<.*?>>', '', text)
    text = re.sub(r'<</.*?>>', '', text)
    
    # 7. Normalize line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    # 8. Create text segment if needed
    if text and not text_segments:
        text_segments = [{"Text": text, "ConditionID": make_always_condition()}]
    elif text and text_segments:
        text_segments.append({"Text": text, "ConditionID": make_always_condition()})
    
    # 9. Apply formatting to each segment
    for segment in text_segments:
        segment['Text'] = apply_formatting(segment['Text'])
    
    # 10. Remove trailing \n and whitespace
    for segment in text_segments:
        segment['Text'] = segment['Text'].rstrip('\n').rstrip()
    
    # 11. Set AutoTransition for nodes with single choice
    if len(all_choices) == 1:
        all_choices[0]['AutoTransition'] = True
    
    # 12. Build final structure
    final_node = {
        "RowName": node['NodeID'],
        "TextSegments": text_segments if text_segments else [{"Text": "", "ConditionID": make_always_condition()}],
        "Actions": actions,
        "Choices": all_choices
    }
    
    return final_node

def make_always_condition():
    """Create an 'Always true' condition structure"""
    return {
        "Type": "Always",
        "VariableName": "",
        "Operator": "",
        "Value": ""
    }

def detect_type(value):
    """Detect value type for Operation name"""
    if value.lower() in ['true', 'false']:
        return 'Bool'
    elif '.' in value:
        try:
            float(value)
            return 'Float'
        except:
            return 'String'
    else:
        try:
            int(value)
            return 'Int'
        except:
            return 'String'

def extract_actions(text):
    """Extract <<set>> and <<unset>> actions"""
    actions = []
    
    set_pattern = r'<<set\s+\$(\w+)\s*(=|\+=|-=)\s*([^>]+)>>'
    for match in re.finditer(set_pattern, text):
        var_name = match.group(1)
        operator = match.group(2)
        value = match.group(3).strip().strip('"')
        value_type = detect_type(value)
        
        if operator == '=':
            operation = f"SET_{value_type}"
        elif operator == '+=':
            operation = f"ADD_{value_type}"
        elif operator == '-=':
            operation = f"SUB_{value_type}"
        
        actions.append({
            "VariableName": var_name,
            "Operation": operation,
            "Value": value
        })
    
    unset_pattern = r'<<unset\s+\$(\w+)>>'
    for match in re.finditer(unset_pattern, text):
        var_name = match.group(1)
        actions.append({
            "VariableName": var_name,
            "Operation": "UNSET",
            "Value": ""
        })
    
    return actions

def extract_inline_actions(inline_macros):
    """Extract actions from inline macros string"""
    actions = []
    if not inline_macros:
        return actions
    
    # Pattern 1: Full format <<set $var = value>>
    set_pattern = r'<<set\s+\$(\w+)\s*(=|\+=|-=)\s*([^>]+)>>'
    for match in re.finditer(set_pattern, inline_macros):
        var_name = match.group(1)
        operator = match.group(2)
        value = match.group(3).strip().strip('"')
        value_type = detect_type(value)
        
        if operator == '=':
            operation = f"SET_{value_type}"
        elif operator == '+=':
            operation = f"ADD_{value_type}"
        elif operator == '-=':
            operation = f"SUB_{value_type}"
        
        actions.append({
            "VariableName": var_name,
            "Operation": operation,
            "Value": value
        })
    
    # Pattern 2: Short format [$var = value] or [$var+=value]
    short_set_pattern = r'\[\$(\w+)\s*(=|\+=|-=)\s*([^\]]+)\]'
    for match in re.finditer(short_set_pattern, inline_macros):
        var_name = match.group(1)
        operator = match.group(2)
        value = match.group(3).strip().strip('"')
        value_type = detect_type(value)
        
        if operator == '=':
            operation = f"SET_{value_type}"
        elif operator == '+=':
            operation = f"ADD_{value_type}"
        elif operator == '-=':
            operation = f"SUB_{value_type}"
        
        actions.append({
            "VariableName": var_name,
            "Operation": operation,
            "Value": value
        })
    
    # Pattern 3: Full format <<unset $var>>
    unset_pattern = r'<<unset\s+\$(\w+)>>'
    for match in re.finditer(unset_pattern, inline_macros):
        var_name = match.group(1)
        actions.append({
            "VariableName": var_name,
            "Operation": "UNSET",
            "Value": ""
        })
    
    return actions

def parse_link(link_content):
    """Parse link content like 'Text|Node][$var=5][$var2+=1'
    Returns: (choice_text, next_node, inline_macros_string)
    """
    # Find inline macros at the end: ][...][...]
    inline_pattern = r'\]((?:\[[^\]]+\])*)$'
    inline_match = re.search(inline_pattern, link_content)
    
    inline_macros = ""
    base_content = link_content
    
    if inline_match:
        inline_macros = inline_match.group(1)  # ][...][...]
        base_content = link_content[:inline_match.start()]  # Text|Node
    
    # Parse base content
    if '|' in base_content:
        parts = base_content.split('|', 1)
        choice_text = parts[0].strip()
        next_node = parts[1].strip()
    elif '->' in base_content:
        parts = base_content.split('->', 1)
        choice_text = parts[0].strip()
        next_node = parts[1].strip()
    elif '<-' in base_content:
        parts = base_content.split('<-', 1)
        next_node = parts[0].strip()
        choice_text = parts[1].strip()
    else:
        choice_text = base_content.strip()
        next_node = base_content.strip()
    
    return choice_text, next_node, inline_macros

def process_if_conditions(text, choices_list):
    """Process <<if>> constructs"""
    segments = []
    
    if_pattern = r'<<if\s+(.+?)>>(.*?)<<endif>>'
    
    def process_if_block(match):
        condition_expr = match.group(1).strip()
        block_content = match.group(2)
        
        condition_id = parse_condition(condition_expr)
        
        # Find all links in block
        links_in_block = re.findall(r'\[\[(.*?)\]\]', block_content)
        
        for link_content in links_in_block:
            choice_text, next_node, inline_macros = parse_link(link_content)
            inline_actions = extract_inline_actions(inline_macros)
            
            choices_list.append({
                "ChoiceText": choice_text,
                "NextNodeID": next_node,
                "ConditionID": condition_id,
                "AutoTransition": False,
                "InlineActions": inline_actions,
                "InlineText": ""
            })
        
        # Extract text and clean it
        text_in_block = re.sub(r'\[\[.*?\]\]', '', block_content)
        text_in_block = re.sub(r'<<.*?>>', '', text_in_block)
        text_in_block = text_in_block.strip()
        text_in_block = text_in_block.rstrip('\n').rstrip()
        
        if text_in_block:
            segments.append({"Text": text_in_block, "ConditionID": condition_id})
        
        return ''
    
    text = re.sub(if_pattern, process_if_block, text, flags=re.DOTALL)
    
    return segments, text

def parse_condition(expr):
    """Parse condition and return structured dict"""
    expr = expr.strip()
    
    # 1. Check for comparison operators FIRST
    operators = ['>=', '<=', '!=', '==', '>', '<']
    for op in operators:
        if op in expr:
            parts = expr.split(op, 1)
            var_name = parts[0].strip().lstrip('$')
            value = parts[1].strip()
            return {
                "Type": "Comparison",
                "VariableName": var_name,
                "Operator": op,
                "Value": value
            }
    
    # 2. Check for 'not' operator
    if expr.startswith('not '):
        var_name = expr[4:].strip().lstrip('$')
        return {
            "Type": "NotBool",
            "VariableName": var_name,
            "Operator": "",
            "Value": ""
        }
    
    # 3. Simple boolean variable
    if expr.startswith('$'):
        var_name = expr[1:].strip()
        return {
            "Type": "Bool",
            "VariableName": var_name,
            "Operator": "",
            "Value": ""
        }
    
    # 4. Fallback
    var_name = expr.replace(' ', '').lstrip('$')
    return {
        "Type": "Bool",
        "VariableName": var_name,
        "Operator": "",
        "Value": ""
    }

def extract_choices(text):
    """Extract links [[...]] from text"""
    choices = []
    
    text_no_if = re.sub(r'<<if.*?>>.*?<<endif>>', '', text, flags=re.DOTALL)
    
    # Use new regex that captures inline macros
    link_pattern = r'\[\[(.+?)\]((?:\[[^\]]+\])*)\]'
    
    for match in re.finditer(link_pattern, text_no_if):
        link_content = match.group(1)
        inline_macros = match.group(2)
        
        choice_text, next_node, _ = parse_link(link_content)
        inline_actions = extract_inline_actions(inline_macros)
        
        choice = {
            "ChoiceText": choice_text,
            "NextNodeID": next_node,
            "ConditionID": make_always_condition(),
            "AutoTransition": False,
            "InlineActions": inline_actions,
            "InlineText": ""
        }
        
        choices.append(choice)
    
    return choices

def apply_formatting(text):
    """Apply formatting to text - UE Rich Text Block syntax"""
    text = re.sub(r'__(.+?)__', r'<b>\1</>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</>', text)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</>', text)
    
    return text

if __name__ == "__main__":
    if len(sys.argv) != 3:
        log_error("Usage: python 04_transform.py <input> <output>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        log_error(f"File not found: {input_file}")
        sys.exit(1)
    
    transform(input_file, output_file)