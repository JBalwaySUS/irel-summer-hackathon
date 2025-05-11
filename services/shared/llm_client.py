# LLM utility for Groq API interactions
import os
import groq
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self):
        self.client = groq.AsyncClient(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Default Llama model from Groq

    async def generate_response(self, system_prompt, user_prompt, temperature=0.7):
        """
        Generate a response from the LLM model
        
        Args:
            system_prompt: Instructions for the model
            user_prompt: User's query or input
            temperature: Controls randomness (0-1)
            
        Returns:
            str: Generated response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating LLM response: {str(e)}")
            return None