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

import os, random, json, re

# DEBUG flag inherited from OPTIONS.json
_options_path = os.path.join(os.path.dirname(__file__), "OPTIONS.json")
DEBUG = False
with open(_options_path, "r") as _f:
    _options = json.load(_f)
    DEBUG = _options.get("DEBUG", False)

traits_lib = {}
with open("random_traits_lib.json","r") as f:
    traits_lib = json.load(f)

pattern = re.compile(r'\$(.*?)(?=[ a-z]|$)') # subrandomizer detection pattern ($ followed by any non-lowercase, non-spaces text)
def subrandomize(table_name) -> str:
    """Given a table name in the random_traits_lib, select a random item from the table."""
    if table_name not in traits_lib:
        print("Table name not found in traits lib!")
        return ""
    choices = traits_lib[table_name] if type(traits_lib[table_name]) == list else list(traits_lib[table_name].keys()) # assume if not list, we're working with a dict
    return random.choice(choices)

def generate_random_agent_prompt(name) -> str:
    """Generate a random agent prompt using traits from the traits library."""
    agent_prompt = ""
    adjective = random.choice(list(traits_lib["ADJECTIVES"].keys()))
    role = random.choice(list(traits_lib["ROLES"].keys()))
    goal = traits_lib["ROLES"][role]["GOAL"]
    introduction = f"You are {name}. In this conversation, your role is the {adjective} {role}. Your goal is to {goal}"
    agent_prompt += introduction + "\n\n"
    agent_prompt += "Traits and Behaviors:\n"
    traits = traits_lib["ADJECTIVES"][adjective] + traits_lib["ROLES"][role]["TRAITS"]
    for trait in traits:
        agent_prompt += f"- {trait}\n"
    extra_trait = random.choice(traits_lib["FLAVOR_TRAITS"])
    agent_prompt += f"- {extra_trait}\n"
    # Replace any instances of subrandomizable content (indicated by "$")
    matches = set(pattern.findall(agent_prompt)) # Preserve only unique values
    for match in matches:
        replacement = subrandomize(match).lower()
        if DEBUG: print(f"[DEBUG] Replacing {match} with {replacement}!")
        agent_prompt = agent_prompt.replace("$"+match,replacement)
    return agent_prompt

def generate_random_agent_prompt_dnd(name, is_animal_fantasy=False) -> str:
    """Generate a random agent prompt for agentic D&D players."""
    agent_prompt = ""
    dnd_class = random.choice(list(traits_lib["CLASSES_DND"].keys()))
    is_caster = dnd_class in ["Wizard","Sorcerer","Druid","Cleric","Bard","Paladin","Ranger","Warlock","Artificer"]
    species : str = random.choice(list(traits_lib["SPECIES_DND" if not is_animal_fantasy else "SPECIES_ANIMAL"].keys()))
    species_trait = traits_lib["SPECIES_DND" if not is_animal_fantasy else "SPECIES_ANIMAL"][species]
    if species.capitalize() in ["BEAR","CANINE","FELINE","LIZARD","BIRD","FISH","INSECT","UNGULATE"]:
        species = random.choice(traits_lib["RANDOM_" + species.capitalize()])
    adjective = random.choice(list(traits_lib["ADJECTIVES"].keys()))
    role = random.choice(list(traits_lib["ROLES"].keys()))
    goal = traits_lib["ROLES"][role]["GOAL"]
    introduction = f"You are {name}, a {species} {dnd_class}. In this adventure, your role is the {adjective} {role}. Your goal is to {goal}"
    agent_prompt += introduction + "\n\n"
    # Speech + Traits
    agent_prompt += "Traits and Behaviors:\n"
    traits : list = traits_lib["ADJECTIVES"][adjective] + traits_lib["ROLES"][role]["TRAITS"] + [random.choice(traits_lib["FLAVOR_TRAITS"])]
    for trait in traits:
        agent_prompt += f"- {trait}\n"
    agent_prompt += "\n"
    # Mechanical abilities
    class_features = traits_lib["CLASSES_DND"][dnd_class]
    agent_prompt += "Special Abilities:\n"
    for feature in (class_features["FEATURES"] + species_trait):
        agent_prompt += f"- {feature}\n"
    agent_prompt += "You can use each of your special abilities once per encounter" + ("." if not is_caster else ", except for Spellcasting. You have a well of magic energy and can use Spellcasting until this well is depleted. At the end of each day, your magic energy replenishes.") + "\n\n"
    # Spell list
    if is_caster:
        agent_prompt += "Spell List:\n"
        for spell in class_features["SPELLS"]:
            agent_prompt += f"- {spell}\n"
    # Replace any instances of subrandomizable content (indicated by "$")
    matches = set(pattern.findall(agent_prompt)) # Preserve only unique values
    for match in matches:
        replacement = subrandomize(match).lower()
        if DEBUG: print(f"[DEBUG] Replacing {match} with {replacement}!")
        agent_prompt = agent_prompt.replace("$"+match,replacement)
    return agent_prompt

def generate_prompts(prompt_count = 6, is_dnd=True, is_animal_fantasy=False):
    """Generate random prompt files for AI agents. By default, this generates 6 prompts for AI-plays-D&D style games."""
    agent_names = _options.get("AGENT_NAMES")
    for i in range(0,prompt_count):
        # Generate prompt with placeholder name
        prompt = generate_random_agent_prompt(agent_names[i]) if not is_dnd else generate_random_agent_prompt_dnd(agent_names[i],is_animal_fantasy)
        # Write prompt to file
        with open(f"prompts/AGENT_{i+1}_PROMPT.txt","w") as f:
            f.write(prompt)