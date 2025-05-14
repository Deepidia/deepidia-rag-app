import openai
from config.config import OPENAI_API_KEY, GEMINI_API_KEY
import google.generativeai as genai
from typing import Optional

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

    def generate_viral_ideas(self, topic_type: str, scope: str, keyword: Optional[str], num_ideas: int = 5):
        if not isinstance(num_ideas, int) or num_ideas < 1:
            raise ValueError("num_ideas must be a positive integer")
        if not scope.strip():
            raise ValueError("scope cannot be empty")
        if scope not in VALID_TOPIC_TYPES:
            raise ValueError(
                f"Invalid scope type: {scope}. Must be one of: {VALID_TOPIC_TYPES}"
            )

        if self.model_type == "openai":
            return self._generate_with_openai(topic_type, scope, keyword, num_ideas)
        elif self.model_type == "gemini":
            return self._generate_with_gemini(topic_type, scope, keyword, num_ideas)
        else:
            raise ValueError(f"Invalid model type: {self.model_type}")
        
    def _construct_prompt(self, topic_type: str, scope: str, keyword: Optional[str], num_ideas: int):
        """
        Constructs the dynamic prompt to generate structured viral ideas.
        """
        base_prompt = f"""You are an expert in content creation, social media trends, and viral marketing. Generate {num_ideas} viral topic ideas to reach the target audience.

    For each idea, provide:
    title: [Catchy, attention-grabbing title]
    description: [Brief, engaging description]

    Category: {topic_type}
    Scope: {scope}"""

        if keyword:
            base_prompt += f"\nKeyword: {keyword}"
        
        base_prompt += "\n\nFormat each idea exactly as shown above, with 'title:' and 'description:' on separate lines. Separate each idea with a blank line."
        
        return base_prompt

    
    def _generate_with_openai(self, topic_type: str, scope: str, keyword: str, num_ideas: int):
        try:
            prompt_text = self._construct_prompt(topic_type, scope, keyword, num_ideas)
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert idea generator."},
                    {"role": "user", "content": prompt_text},
                ],
                max_tokens=400,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=None,
            )
            content = response.choices[0].message["content"].strip()

            
            ideas = content.split("\n")
            return self._clean_generated_ideas(ideas, num_ideas)
        except Exception as e:
            raise RuntimeError(f"Error generating viral ideas with OpenAI: {str(e)}")

    def _generate_with_gemini(self, topic_type: str, scope: str, keyword: str, num_ideas: int):
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = self._construct_prompt(topic_type, scope, keyword, num_ideas)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=1.0,
                    max_output_tokens=400,
                )
            )
            raw_response = response.text.strip()
            ideas = raw_response.split("\n")
            return self._clean_generated_ideas(ideas, num_ideas)
        except Exception as e:
            raise RuntimeError(f"Error generating viral ideas with GEMINI: {e}")

    def _clean_generated_ideas(self, ideas, num_ideas):
        """
        Cleans and formats the generated ideas into a structured list.
        """
        structured_ideas = []
        current_idea = {}
        
        for line in ideas:
            line = line.strip()
            if not line:
                if current_idea:
                    structured_ideas.append(current_idea)
                    current_idea = {}
                continue
                
            if line.startswith('title:'):
                current_idea['title'] = line[6:].strip()
            elif line.startswith('description:'):
                current_idea['description'] = line[12:].strip()
        
        # Add the last idea if exists
        if current_idea:
            structured_ideas.append(current_idea)
        
        return structured_ideas[:num_ideas]
