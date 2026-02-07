SYSTEM_INTRO = ""
SYSTEM_OUTRO = ""
AGENT_1_BODY = ""
AGENT_2_BODY = ""
AGENT_3_BODY = ""
AGENT_4_BODY = ""
AGENT_5_BODY = ""
AGENT_6_BODY = ""
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
with open("prompts/AGENT_4_PROMPT.txt") as f:
    AGENT_4_BODY = f.read()
with open("prompts/AGENT_5_PROMPT.txt") as f:
    AGENT_5_BODY = f.read()
with open("prompts/AGENT_6_PROMPT.txt") as f:
    AGENT_6_BODY = f.read()

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

# Agent 4
AGENT_4 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_4_BODY}
    {SYSTEM_OUTRO}
'''}

# Agent 5
AGENT_5 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_5_BODY}
    {SYSTEM_OUTRO}
'''}

# Agent 6
AGENT_6 = {"role": "system", "content": f'''
    {SYSTEM_INTRO}
    {AGENT_6_BODY}
    {SYSTEM_OUTRO}
'''}

def generate_random_agent_prompt(name) -> str:
    """Generate a random agent prompt using traits from the traits library."""
    agent_prompt = ""
    import random, json
    traits_lib = {}
    with open("random_traits_lib.json","r") as f:
        traits_lib = json.load(f)
    dnd_class = random.choice(traits_lib["CLASSES_DND"])
    species = random.choice(traits_lib["SPECIES_DND"])
    adjective = random.choice(traits_lib["ADJECTIVES"])
    role = random.choice(traits_lib["ROLES"])
    introduction = f"You are {name}, a {species} {dnd_class}. In this conversation, your role is the {adjective} {role}."
    agent_prompt += introduction + "\n\n"
    agent_prompt += "Traits and Behaviors:\n"
    if role in traits_lib["ROLE_TRAITS"]:
        traits = traits_lib["ROLE_TRAITS"][role]
        for trait in traits:
            agent_prompt += f"- {trait}\n"
    if adjective in traits_lib["ADJECTIVE_TRAITS"]:
        traits = traits_lib["ADJECTIVE_TRAITS"][adjective]
        for trait in traits:
            agent_prompt += f"- {trait}\n"
    extra_trait = random.choice(traits_lib["FLAVOR_TRAITS"])
    agent_prompt += f"- {extra_trait}\n"
    return agent_prompt