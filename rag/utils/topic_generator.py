import openai
from config.config import OPENAI_API_KEY, GEMINI_API_KEY
import google.generativeai as genai
from langchain.prompts import ChatPromptTemplate

VALID_TOPIC_TYPES = [
    "All Topics",
    "Trending Now",
    "Most Researched",
    "Emerging Fields",
    "Future Oriented",
]


class ViralTopicGenerator:
    def __init__(self, model_type: str = "openai"):
        self.model_type = model_type.lower()
        self.api_key = self.get_api_key()
        self.setup_model()

    def get_api_key(self):
        if self.model_type == "openai":
            return OPENAI_API_KEY
        elif self.model_type == "gemini":
            return GEMINI_API_KEY
        else:
            raise ValueError(f"Invalid model type: {self.model_type}")

    def setup_model(self):
        if self.model_type == "openai":
            openai.api_key = self.api_key
        elif self.model_type == "gemini":
            genai.configure(api_key=self.api_key)

    def generate_viral_ideas(self, topic_type: str, num_ideas: int = 5):
        if topic_type not in VALID_TOPIC_TYPES:
            raise ValueError(
                f"Invalid topic type: {topic_type}. Must be one of: {VALID_TOPIC_TYPES}"
            )

        if self.model_type == "openai":
            return self._generate_with_openai(topic_type, num_ideas)
        elif self.model_type == "gemini":
            return self._generate_with_gemini(topic_type, num_ideas)
        else:
            raise ValueError(f"Invalid model type: {self.model_type}")

    def _generate_with_openai(self, topic_type: str, num_ideas: int):
        try:
            # Constructing the dynamic prompt
            prompt_text = self._construct_prompt(topic_type, num_ideas)

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # Using the gpt-4o-mini model
                messages=[
                    {"role": "system", "content": "You are an expert idea generator."},
                    {"role": "user", "content": prompt_text},
                ],
                max_tokens=400,  # Adjusted for multiple ideas
                temperature=0.7,  # Creativity control
                top_p=1.0,  # Sampling method
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=None,  # Allows full completion
            )

            # Extracting the text from the response
            content = response.choices[0].message["content"].strip()
            ideas = content.split("\n")

            # Cleaning and formatting ideas
            cleaned_ideas = self._clean_generated_ideas(ideas, num_ideas)
            return cleaned_ideas
        except openai.error.OpenAIError as e:
            raise RuntimeError(f"OpenAI API Error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error generating viral ideas with OpenAI: {str(e)}")

    def _generate_with_gemini(self, topic_type: str, num_ideas: int):

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")

            prompt = f"Generate {num_ideas} viral ideas for the topic: {topic_type}"

            response = model.generate_content(prompt)
            raw_response = response.text.strip()
 
            ideas = raw_response.split("\n")
        
            # Cleaning and formatting ideas
            cleaned_ideas = self._clean_generated_ideas(ideas, num_ideas)
            return cleaned_ideas
        
        except Exception as e:
            raise RuntimeError(f"Error generating viral ideas with GEMINI: {e}")

    def _construct_prompt(self, topic_type: str, num_ideas: int):
        """
        Constructs the dynamic prompt based on the topic type and number of ideas.
        """
        return f"Generate {num_ideas} viral content ideas for the topic: {topic_type}. Each idea should be clear, engaging, and suitable for a wide audience."

    def _clean_generated_ideas(self, ideas, num_ideas):
        """
        Cleans and formats the generated ideas.
        - Removes empty ideas.
        - Limits the number of ideas to num_ideas.
        """
        cleaned_ideas = [idea.strip() for idea in ideas if idea.strip()]
        return cleaned_ideas[:num_ideas]
