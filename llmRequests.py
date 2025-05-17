from openai import OpenAI
from dotenv import load_dotenv
import os

#Using .env to store API key
load_dotenv()

class gptPrompting:
    #Initializes client
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("api_key"))

    #Allows for GPT prompting (General function for future additons if needed)
    def askGptText(self, prompt, model="gpt-4o-mini"):
        return self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content

    #Filter check for both user questions and user prompts to ensure content is relatively appropriate.
    def filter(self, prompt):
        filterCheck = self.askGptText(
            f"""
            Please ONLY either say "True" or "False" of whether the given prompt falls within the criteria of being an appropriate topic, like it's not harmful or just innapropriate..
            Here is the prompt:
            {prompt}
            """
        )
        
        #If the value is anything other than "true", then it returns false.
        return filterCheck.strip().lower() == "true"

        

    #Generates prompts from user given prompt
    def promptGenerator(self, prompt):
        generatedPrompts = self.askGptText(f"""
            Please generate 3 new related prompts to the user's entered prompt: {prompt}.
            Some stipulations:
            1. Keep the prompt length similar.
            2. Vary the tone (e.g., academic, casual, focused).
            3. Maintain the original prompt's meaning and intent.
            4. Format the prompts like this: prompt1::prompt2::prompt3
        """)
        return generatedPrompts
    
    #Generate the quiz and formats it such to be processed into a list later.
    def quizGeneration(self, largeSummary):
        return self.askGptText(f"""Here are the links I have selected: {largeSummary}
            Can you generate 5 questions to quiz my understanding of the topics found in these links?
            Make these multiple choice with 1 correct and 3 incorrect answers.
            Format them like:
            1. question::answer1(correct)::answer2::answer3::answer4
            2. question::answer1::answer2::answer3(correct)::answer4
            etc.
            """)


    
    