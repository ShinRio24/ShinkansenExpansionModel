csv_file = '/content/drive/MyDrive/worldcities.csv'
#this cell stores all the prompts which will be fed into the LLM
#this prompt is for initial idea generation, following the examplme of the SAKANA AI AI SCIENTIST model
idea_first_prompt = """
Here are the ideas that you have already generated:

'''
{prev_ideas_string}
'''

Come up with the next rail expansion project for the japanese Shinkansen

Respond in the following format:

THOUGHT:
<THOUGHT>

NEW IDEA JSON:
```json
<JSON>
```

In <THOUGHT>, first briefly discuss your intuitions and motivations for the idea. Detail your high-level plan and any potential challenges. Justify how the idea could benefit the population of japan.

In <JSON>, provide the new idea in JSON format with the following fields:
- "Name": A shortened descriptor of the idea. Lowercase, no spaces, underscores allowed.
- "Starting City": The City which the rail for the expansion plan will start at
- "Ending City": The City which the rail for the expansion plan will end at
- "Impact": Estimation of the amount of daily users or improvement of QOL
- "Cost": A estimation of costs in dollars
- "Challenges": Any potential Challenges (such as mountains you have to go around, rivers, etc)
- "Accesssibility": Evaluate the current accessibility of this location (other high speed rail, highways, etc)

Be cautious and realistic on your ratings.
This JSON will be automatically parsed, so ensure the format is precise.
You will have {num_reflections} rounds to iterate on the idea, but do not need to use them all.
"""

#this prompt is for the idea refinement / reflection, again, following the AI SCIENTIST format
idea_reflection_prompt = """Round {current_round}/{num_reflections}.
In your thoughts, first carefully consider the quality, impact, and feasibility of the idea you just created.
Include any other factors that you think are important in evaluating the idea.
Ensure the idea is clear and concise, and the JSON is the correct format.
Do not make things overly complicated.
In the next attempt, try and refine and improve your idea.
Stick to the spirit of the original idea unless there are glaring issues.

Respond in the same format as before:
THOUGHT:
<THOUGHT>

NEW IDEA JSON:
```json
<JSON>
```

If there is nothing to improve, simply repeat the previous JSON EXACTLY after the thought and include "I am done" at the very end of your response.
ONLY INCLUDE "I am done" IF YOU ARE MAKING NO MORE CHANGES."""

#this prompt is used to generate an estimation on distance and cost per mile of suggested rail, utilizing data from
#past rail projects and having the LLM use this data as a basis
#for its rough estimation
priceEstimation="""
Given this following data of Japanese Shinkansen rail building costs, (name of expansion: price in japanese billion yen per km) evaluate the current project (will be given at the very end) and determine a more accurate cost in billion yen.
Remeber you need to consider the terain the rail is passing, such as mountians, rivers, cities, etc
MAKE SURE YOU OUTPUT THE FOLLOWING JSON FILE

Respond in the following format:
total:
```json
<JSON>
```
In <JSON>, provide the new idea in JSON format with the following fields:
- "totalCost": estimated price / cost of the whole plan in USD

Tokaido	3.09
Sanyo	2.99
Tohoku (Omiya-Morioka)	6.76
Tohoku (Omiya-Ueno)	25.89
Tohoku (Ueno-Tokyo)	36.71
Tohoku (Morioka-	4.91
Hachinohe)
Jõetsu (Omiya-Niigata)	9.74
Hokuriku (Takasaki-	7.17
Nagano)
Kyusha (Shin-Yatsushiro-	5.07
Kagoshima-Chuõ)
Yamagata (Fukushima-Yamagata)	0.44
Yamagata (Yamagata-Shinjo)	0.55
Akita (Morioka-Akita)	0.47"""

#following format used to give the LLM a template to write the final writeup, mostly inspired from the AI SCIENTIST example
per_section_tips = {
    "Abstract": """
- TL;DR of the rail expansion plan.
- What new rail routes or improvements are we proposing and why are they important?
- What challenges or obstacles make this expansion plan difficult to achieve?
- What is the impact of these changes? (i.e. how will these expansions improve transportation, accessibility, etc.?)
- Numerical impact - bring up the population impact brought in ideas file

Ensure the abstract presents a clear, concise overview and motivates why this project is valuable. This should be one continuous paragraph with no breaks between lines.
""",
    "Introduction": """
- A detailed version of the abstract, explaining the proposed rail expansion plan in full.
- What new routes or improvements are we proposing and why are they significant?
- What challenges need to be overcome to implement this plan successfully?
- What are the broader impacts of the expansion? (i.e. environmental benefits, economic growth, social accessibility, etc.)
- New trend: list the key features and objectives of the rail expansion plan as bullet points.
- Extra space? Future work: discuss possible future expansions or improvements!
""",
    "Related Work": """
- Existing transportation and rail projects that aim to solve similar problems or enhance transit systems.
- Goal is to “compare and contrast” – how do other rail expansions differ in terms of location, design, or objectives? If applicable, provide a comparison to highlight how this new plan offers unique solutions.
- Note: Don’t just describe other projects. Discuss why their methods or strategies might not work for this particular expansion or why they’re relevant to our context.
""",
    "Method": """
- Detailed description of the rail expansion plan. What exactly will be done? Why is it being done?
- Discuss the planning, design, and logistics of the expansion, with clear references to any data or research used to support the project.
- Lay out how the design fits within existing transportation frameworks, including cost estimates and resource allocation.
""",
    "Implementation Plan": """
- How do we turn this rail expansion plan into reality?
- Describe the timeline, key stakeholders, project phases, and how the plan will be executed.
- Include detailed information about the locations, routes, stations, and any technological infrastructure needed for the plan.
- Consider environmental factors, public feedback, and other practical challenges in executing the plan.
- Include numerical impact as derived from files given
""",
    "Results": """
- Analyze the potential impact of the rail expansion plan based on available data and simulations.
- Discuss the expected benefits, such as reduced congestion, improved accessibility, or economic growth.
- Include comparisons with existing infrastructure or alternative expansion proposals, providing relevant statistics and projections.
- If applicable, conduct feasibility studies or highlight any key challenges or uncertainties in the project.
- Include visual aids (maps, charts, etc.) to show projected outcomes and compare different scenarios.
""",
    "Conclusion": """
- Summarize the key takeaways from the rail expansion plan.
- Reflect on the main objectives, challenges, and potential outcomes.
- Future work: Discuss possible future expansions, upgrades, or improvements to the rail system as the project progresses.
""",
}

#HELPER METHOD

#method taken directly from AI Scientist, extracrt json from LLM response
import re
def extract_json_between_markers(llm_output):
    # Regular expression pattern to find JSON content between ```json and ```
    json_pattern = r"```json(.*?)```"
    matches = re.findall(json_pattern, llm_output, re.DOTALL)

    if not matches:
        # Fallback: Try to find any JSON-like content in the output
        json_pattern = r"\{.*?\}"
        matches = re.findall(json_pattern, llm_output, re.DOTALL)

    for json_string in matches:
        json_string = json_string.strip()
        try:
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError:
            # Attempt to fix common JSON issues
            try:
                # Remove invalid control characters
                json_string_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
                parsed_json = json.loads(json_string_clean)
                return parsed_json
            except json.JSONDecodeError:
                continue  # Try next match

    return None  # No valid JSON found

#imports database (stored in google drive)
#gets data regarding population of all world cities, saves only japanese cities into dictionary jList
#data from https://simplemaps.com/data/world-cities
import json
import csv

#opens CSV datafile, returning as list
def csv_to_dict(csv_file_path):
    data = []
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data


#stores only the japanese cities into dictionary titled 'jList'
dict_data = csv_to_dict(csv_file)
print(1)
jList={}
for x in dict_data:
  if x['country']=='Japan':
    jList[x['city_ascii']]=x

#this is the main code block that runs the SHINKANSEN RAIL EXPANSION PLANNER


#import necessary libraries
from posixpath import curdir
import json
import os.path as osp
from fuzzywuzzy import fuzz

#these are set strings,
numImprove = 5
numIdeas = 1
prev_ideas_strings=" "

#this is method outputs the string in dictionary closest to target_string
#this is used for finding population of suggested cities, as the database requires exact wording of city to find its population
#because of the uncertainty of LLM's, it could return with inconsistent spacing, special characters etc
def find_closest(target_string, dictionary):
    closest_string = ""
    max_similarity = 0

    for key in dictionary.keys():
        similarity = fuzz.ratio(target_string, key)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_string = key
    return closest_string

#puts inputString into LLM
#function can be changed based on LLM accessibility
#currently configured to manually input into a web browser of chat GPT, putting the LLM's output into the input for this program
def runLLM(inputString):
  print(inputString)
  outputString= input()
  return outputString

#use prompt formatted above to generate new ideas for shinkansen rail expansion plans
#returns raw output of LLM
def generateIdea():
  idea=runLLM(idea_first_prompt.format(
        prev_ideas_string=prev_ideas_strings,
        num_reflections=numImprove,
    ))
  return idea

#use prompt formatted above to revise and reflect on the idea.
def improveIdea(y):
  idea = runLLM(idea_reflection_prompt.format(
        prev_ideas_string=prev_ideas_strings,
        num_reflections=numImprove,
        current_round=y+1,
    ))
  return idea

#Generates and refines plan, return a list containging numIdeas amount of ideas, all in json format as described in formatting above.
def generateIdeas():
  global prev_ideas_strings
  allIdeas=[]
  for x in range(numIdeas):
    idea = generateIdea()

    for y in range(numImprove):
      idea = improveIdea(y)
      if "I am done" in idea.strip():
        break

    print(f"Generated idea {x + 1}/{numIdeas}")

    allIdeas.append(extract_json_between_markers(idea))
    prev_ideas_strings+=str(allIdeas[-1]['Name'])+"\n"
  return allIdeas

#Returns population of the city given in input.
#THIS METOD CURRENTLY ONLY WORKS FOR JAPANESE CITIES
#searches database for city with closest name, returns its population
def getPopulation(x):
  x=find_closest(x,jList)
  return jList[x]['population']

#takes expansion plan formatted in json as expalined in format above
#using priceEstimation prompt, utilizes LLM to estimate total cost of plan, given past examples of costs
def getPrice(x):
  x=runLLM(priceEstimation+str(x))

  return extract_json_between_markers(x)['totalCost']


#utilizing the methods above, estimates the [cost to build]/[population] ratio for each project in an attempt to measure impact
#takes the plan with the highest ratio to the next step
def valueChecker(ideas):
  ratios=[]
  for i,x in enumerate(ideas):
    price=getPrice(x)
    totPeople = getPopulation(x['Starting City']) + getPopulation(x["Ending City"])
    ratios.append([price/int(totPeople),x])
  min_value = min(ratios, key=lambda row: row[0])

  min_value[1]['totalPopulationImpact']=min_value[0]
  return min_value[1]

#utilizing the per_section_tips formatt listed above, creates a writeup of the current plan using an LLM
def createWriteup(idea):

  return runLLM(str(per_section_tips)+str(idea))

#runs the methods above to generate ideas, evaluate them, and preform a writeup on the best idea.
def genNewPlan():
  ideas = generateIdeas()
  topIdea = valueChecker(ideas)
  writeup = createWriteup(topIdea)
  f = open("demofile2.txt", "a")
  f.write(writeup)
  f.close()

#runs the program, creating a report which identifies and evlaulates a possible Japan Rail Shinkansen expansion plan
if __name__ == '__main__':
  genNewPlan()

