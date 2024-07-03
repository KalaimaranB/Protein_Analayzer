import google.generativeai as genai
import json
import logging
import markdown2
import time
import os


class AI_Generator:
    """
    A class to generate AI-based summaries for a list of pathways using Google Generative AI.

    Attributes
    ----------
    pathway_list : str
        A list of pathways to summarize.
    all_good : bool
        A tracker variable if anything went wrong in script
    USAGE_TRACKER_FILE : str
        The file path for tracking API usage.

    Methods
    -------
    __init__(pathway_list):
        Initializes the AI_Generator instance with a list of pathways.

    load_usage_data():
        Loads the API usage data from a file.

    save_usage_data(data):
        Saves the API usage data to a file.

    reset_daily_usage(data):
        Resets the daily API usage data.

    track_usage(request_count, token_count):
        Tracks API usage and ensures it is within the allowed limits.

    get_pathway_summary():
        Generates a summary of the pathways using Google Generative AI.

    get_summaries():
        Retrieves the AI-generated summaries.
    """

    def __init__(self, pathway_list):
        """
        Initializes the AI_Generator instance with a list of pathways.

        Parameters
        ----------
        pathway_list : str
            A list of pathways to summarize.

        """
        self.pathway_list = pathway_list
        self.all_good = True
        self.USAGE_TRACKER_FILE = "usage_tracker.json"

    def load_usage_data(self):
        """
        Loads the API usage data from a file. If the file does not exist, initializes the usage data.

        Returns
        -------
        dict
            A dictionary containing the API usage data.
        """
        if not os.path.exists(self.USAGE_TRACKER_FILE):
            return {
                "requests_per_minute": [],
                "tokens_per_minute": [],
                "requests_per_day": 0,
                "last_reset": time.time(),
            }

        with open(self.USAGE_TRACKER_FILE, "r") as file:
            return json.load(file)

    def save_usage_data(self, data):
        """
        Saves the API usage data to a file.

        Parameters
        ----------
        data : dict
            The API usage data to save.
        """
        with open(self.USAGE_TRACKER_FILE, "w") as file:
            json.dump(data, file)

    def reset_daily_usage(self, data):
        """
        Resets the daily API usage data.

        Parameters
        ----------
        data : dict
            The API usage data to reset.
        """
        data["requests_per_day"] = 0
        data["last_reset"] = time.time()
        self.save_usage_data(data)

    def track_usage(self, request_count, token_count):
        """
        Tracks API usage and ensures it is within the allowed limits.

        Parameters
        ----------
        request_count : int
            The number of API requests being made.
        token_count : int
            The number of tokens being used.

        Returns
        -------
        bool
            True if the usage is within limits, False otherwise.
        """
        data = self.load_usage_data()
        current_time = time.time()

        # Reset daily usage if 24 hours have passed
        if current_time - data["last_reset"] >= 86400:
            self.reset_daily_usage(data)

        # Update the requests per minute and tokens per minute lists
        data["requests_per_minute"] = [
            t for t in data["requests_per_minute"] if current_time - t < 60
        ]
        data["tokens_per_minute"] = [
            t for t in data["tokens_per_minute"] if current_time - t < 60
        ]

        # Check if usage limits are exceeded
        if (
            len(data["requests_per_minute"]) + request_count > 15
            or len(data["tokens_per_minute"]) + token_count > 1_000_000
            or data["requests_per_day"] + request_count > 1500
        ):
            return False  # Usage limits exceeded

        # Update usage data
        data["requests_per_minute"].extend([current_time] * request_count)
        data["tokens_per_minute"].extend([current_time] * token_count)
        data["requests_per_day"] += request_count

        self.save_usage_data(data)
        return True  # Usage is within limits

    def get_pathway_summary(self):
        """
        Generates a summary of the pathways using Google Generative AI.

        Returns
        -------
        str
            The AI-generated summary in markdown format.
        """
        with open("api.json", "r") as file:
            data = json.load(file)

        genai.configure(api_key=data["key"])
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Define the prompt for generating the summary
        defaultPrompt = (
            "Summarize the list of pathways into a detailed paragraph based on categories. "
            "Briefly describe each category and the pathways involved. Keep this description brief, "
            "you don't need to mention every single pathway (just enough). This summary should not include "
            "other text as it will be directly included in a report that explains context."
        )

        prompt = defaultPrompt + self.pathway_list

        # Accurately count tokens using the count_tokens method
        token_count = (model.count_tokens(prompt)).total_tokens

        # Check if usage is within limits
        if not self.track_usage(1, token_count):
            return "API usage limit reached. Please try again later."

        # Generate the summary
        response = model.generate_content(prompt)
        text = markdown2.markdown(response.text)

        return text

    def get_summaries(self):
        """
        Retrieves the AI-generated summaries.

        Returns
        -------
        dict
            A dictionary containing the pathway summary.
        """
        logging.info("Starting to get AI Summaries")
        pathway_summary = self.get_pathway_summary()
        logging.info("Retrieved AI Summaries")
        return {"pathway_summary": pathway_summary}
