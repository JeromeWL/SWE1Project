import streamlit as st

class currentPageState:
    def __init__(self, state):
        self.state = state
        self.initialize()

    #Initializes all of the streamlit variables
    def initialize(self):
        self.state.setdefault("show_form", False)
        self.state.setdefault("show_links", False)
        self.state.setdefault("selected_keyword", None)
        self.state.setdefault("showOption", False)
        self.state.setdefault("links", [])
        self.state.setdefault("related_words", [])
        self.state.setdefault("links_and_summaries", [])
        self.state.setdefault("summarization", [])
        self.state.setdefault("selected_indices", [])
        self.state.setdefault("summarized_text", '')

    
    #Reinitializes all variables
    def pageReset(self):
        self.state["show_form"] = False
        self.state["show_links"] = False
        self.state["selected_keyword"] = None
        self.state["showOption"] = False
        self.state["links"] = []
        self.state["related_words"] = []
        self.state["links_and_summaries"] = []
        self.state["summarization"] = []
        self.state["selected_indices"] = []
        self.state["summarized_text"] = ''
        self.state["citations"] = ''
