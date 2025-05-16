from googlesearch import search
from summarizer import Summarizer
from dotenv import load_dotenv
import trafilatura
import torch
import streamlit as st

device = torch.device("cpu")
load_dotenv()

class SearchHandler:
    def __init__(self):
        self.num_results = 5
        self.model = Summarizer()
        self.threads = 10
        
        self.blacklisted = [
            "reddit.com",
            "twitter.com",
            "quora.com",
            "medium.com",
            "pinterest.com",
            "facebook.com",
            "instagram.com",
            ".pdf"
        ]

        self.max_links_to_try = 20

    # Google search query
    def searchLinks(self, query):
        return list(search(query, num_results=self.max_links_to_try))

    # Summarization using a transformer model
    def summarize(self, text, num_sentences=3):
        try:
            return self.model(text, num_sentences=num_sentences)
        except Exception as e:
            print(f"Failed to summarize text: {e}")
            return None

    # Main summarization wrapper
    def summarizeArticles(self, urls, numofURLs=5, num_sentences=3):
        # Check if summarization is already in progress, and reset if needed
        if 'summarization_in_progress' in st.session_state and st.session_state.summarization_in_progress:
            # Reset summarization progress if already ongoing
            print("Resetting summarization queue...")
            st.session_state.summarization_in_progress = False 

        st.session_state.summarization_in_progress = True
        summaries = []
        filtered_urls = [url for url in urls if not any(bad in url for bad in self.blacklisted)][:self.max_links_to_try]
        url_store = trafilatura.downloads.add_to_compressed_dict(filtered_urls)

        while not url_store.done:
            bufferlist, url_store = trafilatura.downloads.load_download_buffer(url_store, sleep_time=0.25)

            for url, downloaded in trafilatura.downloads.buffered_downloads(bufferlist, self.threads):
                if not downloaded:
                    continue

                extracted = trafilatura.extract(downloaded)
                if not extracted:
                    continue

                print(f"Generating summary for {url}")
                summary = self.summarize(extracted, num_sentences)
                if summary:
                    summaries.append((url, summary))

                if len(summaries) >= numofURLs:
                    st.session_state.summarization_in_progress = False  # Reset flag when done
                    return summaries

        st.session_state.summarization_in_progress = False  # Reset flag if loop ends
        return summaries
