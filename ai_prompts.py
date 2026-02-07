SYSTEM_INTRO = ""
SYSTEM_OUTRO = ""
AGENT_1_BODY = ""
AGENT_2_BODY = ""
AGENT_3_BODY = ""
with open("prompts/SYSTEM_INTRO.txt") as f:
    SYSTEM_INTRO = f.read()
with open("prompts/SYSTEM_OUTRO.txt") as f:
    SYSTEM_OUTRO = f.read()
with open("prompts/AGENT_1_PROMPT.txt") as f:
    AGENT_1_BODY = f.read()
with open("prompts/AGENT_2_PROMPT.txt") as f:
    AGENT_2_BODY = f.read()
with open("prompts/AGENT_3_PROMPT.txt") as f:
    AGENT_3_BODY = f.read()

# Agent 1
AGENT_1 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_1_BODY}
    {SYSTEM_OUTRO}
'''}

# Agent 2
AGENT_2 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_2_BODY}
    {SYSTEM_OUTRO}
'''}

# Agent 3
AGENT_3 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_3_BODY}
    {SYSTEM_OUTRO}
'''}
