import torch
torch.classes.__path__ = []


import streamlit as st
from dotenv import load_dotenv
import time
from llmRequests import gptPrompting
from pageState import currentPageState
from searchAndScrape import SearchHandler
import re

#Load environment variables (API keys, etc.)
load_dotenv()


#Instantiate helper classes
state = st.session_state
pageState = currentPageState(state)


search = SearchHandler()
gpt = gptPrompting()



# Divide the interface into two tabs
tab1, tab2 = st.tabs(["Search Explorer", "Help"])


## -- SECTION 1, SEARCH ENGINE THINGY -- ##

with tab1:
    st.title("🔍 Academic Search Engine")

    #INPUT THE PROMPT
    enteredPrompt = st.text_input(
        "Enter a Google Search:",
        placeholder="Type something like 'health', 'tech', etc."
    )

    #Slight little adjustment to make it so that the two buttons are about flush with eachother
    #We probably could've found another way but I was lazy sorry.
    col1, col2 = st.columns([1, 1.5])

    # - Portion that handles additional prompt generation - #
    with col1:
        if st.button("Generate Related Words"):
            st.session_state.summarization_in_progress = False
            
            #Resets the entire page if pressed, ensuring that the page resets no matter where in the pipeline you are.
            pageState.pageReset()

            #First check if a prompt is empty.
            if not enteredPrompt:
                st.warning("Please enter a search topic before generating.")

            #Then check if the topic doesn't pass the filter.
            elif not gpt.filter(enteredPrompt):
                st.warning("Topic is not appropriate. Try another one.")

            #If all passes, then we generate 3 additional prompts.
            else:
                resp = gpt.promptGenerator(enteredPrompt)
                prompts = resp.split("::")
                state.related_words = [enteredPrompt] + prompts
                state.show_form = True

    # - Setting handler - #
    with col2:
        options = ["Summarize + Chat", "Self assessment", "Cite a source"]
        typeSelection = st.segmented_control(
            "Options:", options,
            selection_mode="single",
            default="Summarize + Chat"
        )



    # -- RELATED PROMPT GENERATION & SELECTION -- #



    if state.get("show_form"):
        st.subheader("📘 Select a Related Prompt")
        with st.form("word_form"):

            #Choose one of the generated prompts
            choice = st.radio("Choose one:", state.related_words, key="related_word_radio")

            if st.form_submit_button("Submit"):
                state.selected_keyword = choice
                st.success(f"You selected: {choice}")

                #Sanity check
                if not choice:
                    st.error("That option was blank! Please pick another.")

                #Begin summarization of the 5 selected articles.
                else:
                    with st.spinner("Fetching links & summaries… It'll be worth the wait!"):
                        state.links = search.searchLinks(choice)
                        state.links_and_summaries = search.summarizeArticles(state.links)

                    #Update page state to remove the generated prompts and add the select a link section..
                    state.show_links = True
                    state.show_form = False

                    #Force page to update.
                    st.rerun()


    # -- LINK AND SUMMARIZATION SELECTION -- #

    if state.get("show_links"):
        st.subheader("🔗 Select Your Links")
        with st.form("word_form2"):
            
            #Collect the selected checkboxes
            indices = []

            #Loop through the links and summaries that're stored.
            for idx, (url, summary) in enumerate(state.links_and_summaries):

                #Create an expander for each link (indx+1 to avoid 0-4 and give 1-5)
                with st.expander(f"Link {idx+1}", expanded=True):
                    st.markdown(f"**URL:** {url}\n\n**Summary:** {summary}")
                    if st.checkbox("Use this link", key=f"chk_{idx}"):
                        indices.append(idx)

            #When they click submit, check to make sure they selected a link
            if st.form_submit_button("Submit"):
                if not indices:
                    st.warning("Pick at least one link.")

                #Else continue down pipeline
                else:
                    state.selected_indices = indices

                    #Save URLs for later usage
                    state.selected_links = [state.links[i] for i in indices]

                    #Update to remove link selection
                    state.show_links = False
                    state.showOption = True

                    #Refresh page & display success
                    st.success(f"Selected {len(indices)} link(s).")

                    #Force update
                    st.rerun()



    # -- SUMMARIZE AND CHAT -- #    


    # Shared summary creation before either form
    if not state.summarized_text:
        
        #Only get summaries and join them into a single large text summary.
        joined = " ".join(summary for idx, (url, summary) in enumerate(state.links_and_summaries) if idx in state.selected_indices)
        state.summarized_text = search.summarize(joined, num_sentences=8)



    # -- CHAT SECTION -- #


    if state.get("showOption") and typeSelection == "Summarize + Chat":
        with st.form("word_form3"):

            #Page formatting, giving large text summary.
            st.subheader("Here's a summary of your selections!")
            st.markdown(f"You searched for: **{state.selected_keyword}**")
            st.markdown(f"**Overall Selected Summary:**\n{state.summarized_text}")

            #Input box
            question = st.text_input(
                "Ask me any questions about your topic:",
                placeholder="'How does X relate to Y?'"
            )


            if st.form_submit_button("Ask"):
                #Check to make sure input
                if not question:
                    st.warning("Please ask a question.")

                #Make sure it passes the filter..
                elif not gpt.filter(question):
                    st.warning("Question not appropriate. Try another one.")

                #Otherwise submit the user's question to a prompt.
                else:
                    prompt = f"""
                    You're in a position where someone is going to ask you questions about a topic.
                    Keep responses to 2-3 sentences; if too long, ask them to be more specific.
                    Positive tone, clear about possible uncertainty.

                    Topic summary:
                    {state.summarized_text}

                    User question:
                    {question}
                    """
                    answer = gpt.askGptText(prompt)
                    st.success(f"Good question! {answer}")



    # -- QUIZ SECTION -- #


    if state.get("showOption") and typeSelection == "Self assessment":

        # Only generate quiz once
        if "quiz_data" not in st.session_state:

            #Call quiz generation such that it'll be formatted for processing..
            quiz = gpt.quizGeneration(state.summarized_text)

            #Then taking the format we're goign to split it up into sentences.
            #It'll be formated as such:
            #1. Q1..
            #2. Q2..
            #etc...
            questions = re.split(r'\n?\d+\.\s*', quiz.strip())
            questions = [q for q in questions if q.strip()]


            formatted_questions = []
            
            #Takes the questions and formats them into the quiz ready form..
            for q in questions:
                #Removes the formatting between questions and options
                parts = q.strip().split("::")

                #Ensures that there's no spacing between seperation
                question = parts[0].strip()

                #Removes the answer key from options
                choices = [c.replace("(correct)", "").strip() for c in parts[1:]]

                #Finds correct tag
                correct_raw = next((c for c in parts[1:] if "(correct)" in c), None)

                #Cleans The answer again or marks it as missing
                correct = correct_raw.replace("(correct)", "").strip() if correct_raw else "Missing"

                #Adds correct answer to the end to be read later.
                formatted_questions.append([question] + choices + [correct])

            #Saves questions
            st.session_state.quiz_data = formatted_questions

        questions = st.session_state.quiz_data

        if "answers" not in st.session_state:
            st.session_state.answers = {}

        #Creates the quiz
        with st.form("quiz_form"):
            for i, q in enumerate(questions[1:]):
                st.subheader(f"Question {i+1}")
                st.markdown(q[0])
                selected = st.radio("Select an answer:", q[1:5], key=f"radio_{i}")
                st.session_state.answers[i] = selected

            submit_quiz = st.form_submit_button("Submit Quiz")

        #Generates answer section for user to check their answers.
        if submit_quiz:
            score = 0
            st.markdown("---")
            st.header("📊 Results")

            #Loops through answers...
            for i, q in enumerate(questions[1:]):
                user_ans = st.session_state.answers.get(i)
                correct_ans = q[5]

                #Compares the correct answer from end of array with user's choice..
                if user_ans == correct_ans:
                    st.success(f"✅ Question {i+1}: Correct\n\n**Your answer:** {user_ans}")
                    score += 1
                else:
                    st.error(f"❌ Question {i+1}: Incorrect\n\n**Your answer:** {user_ans} \n \n **Correct answer:** {correct_ans}")

            st.markdown("---")
            st.subheader(f"🎯 Final Score: **{score} / 5**")


    # -- SITE A SOURCE -- #



    if state.get("showOption") and typeSelection == "Cite a source":
        if not state.citations:

            #Fairly simple, since chatGPT can now access webpages, it'll just grab the info quickly because of the inconsistency of other citation libraries
            state.citations = gpt.askGptText(f"""Here are the links I have selected: {state.selected_links}
                    Can you generate a MLA citation for each link.
                    Return only the link and then the citation.
                    Your output should look like this:
                                        URL: https://example.com
                                        Citation: Put citation here
                    """)
        st.markdown("📚 Your MLA Citations:")
        st.code(state.citations, language="text")



    # -- HELP TAB -- #


                    
with tab2:
    st.title("Common Questions!")
    with st.expander("How to use the application?"):
        st.markdown(f"""
                    It's fairly simple! To start, there's multiple applications that you're able to use, so go ahead at one of those under the enter a prompt field.\n
                    Once you've decided which mode you want to use, enter a short sentence of what you might look up in google, typically a question.\n
                    Shortly after it looks for appropriate links and generates some short summaries, you'll be able to choose 1-5 links. Which ever ones you feel is most appropriate, you'll be able to select those!\n
                    And finally, once you've submitted the links you want to use for the option you selected earlier, you'll be able to use the tool that was selected!
                """)
        
    with st.expander("Where are the sources gathered from?"):
        st.markdown(f"""
                    We used a google search function and so many of the links that you'll see with the tool also can be found just by 
                    looking up your prompts! We do however filter some specific websites because they're javascriptintensive.
                """)
        
    with st.expander("Is this tool accurate?"):
        st.markdown(f"""
                    We highly recommend you do some fact checking by actually vising the links that you select before using them, this is because while we use powerful tools such as
                    chatGPT and other pretrained transformers, they still can make mistakes!
                """)
        
    with st.expander("Who made the tool?"):
        st.markdown(f"""
                    This project was made by Braden Mau and Will Jerome from University of Wisconsin Eau Claire for a Software Engineering project.
                """)
        
    with st.expander("Is my session private?"):
        st.markdown(f"""
                    Yes it is! Once you refresh the page, you create a new session!
                """)