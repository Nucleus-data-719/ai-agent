import openai
import os
from typing import List, Dict, Optional
import json

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class LeadAgent:
    def __init__(self):
        self.system_prompt = """You are a lead qualification assistant for a real estate company called ABC Properties.

Your goal is to:
1. Understand the customer's property requirements
2. Ask only relevant questions
3. Never pressure the customer
4. Never invent property information
5. Collect contact information when appropriate
6. Keep responses short and conversational (1-3 sentences)

Company Information:
- Name: ABC Properties
- Locations: DHA Lahore, Bahria Town Lahore
- Property types: Houses, Apartments, Plots
- Business hours: 9 AM - 7 PM

Available property types and typical prices:
- 5 Marla House: 1.5-2.5 Crore
- 10 Marla House: 3-5 Crore
- 1 Kanal House: 6-10 Crore
- 5 Marla Plot: 80 Lakh - 1.5 Crore
- 10 Marla Plot: 1.5-3 Crore
- Apartments: 50 Lakh - 2 Crore

When the customer shows high interest, offer to arrange a call with a property consultant.

Always be helpful, friendly, and professional.
"""
        
    def get_conversation_history(self, messages: List[Dict]) -> List[Dict]:
        """Format conversation history for OpenAI"""
        history = [{"role": "system", "content": self.system_prompt}]
        
        for msg in messages:
            history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return history
    
    async def get_response(self, messages: List[Dict]) -> str:
        """Get AI response from OpenAI"""
        try:
            conversation = self.get_conversation_history(messages)
            
            response = openai.chat.completions.create(
                model=MODEL,
                messages=conversation,
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return "I'm having trouble connecting. Please try again or contact our team directly."
    
    def extract_lead_data(self, messages: List[Dict]) -> Dict:
        """Extract structured lead data from conversation"""
        # Convert messages to text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        # Use a separate prompt to extract data
        extraction_prompt = f"""
        Extract the following information from this conversation:
        - name: person's name (full name)
        - phone: phone number
        - email: email address
        - property_type: type (house, apartment, plot)
        - location: area/location
        - size: size in marla/kanal
        - budget: budget amount
        - timeline: when they want to buy (immediate, 1 month, 3 months, etc.)
        - purpose: purpose (family, investment, etc.)
        - bedrooms: number of bedrooms needed
        
        If information is not mentioned, use "null".
        
        Conversation:
        {conversation_text}
        
        Return ONLY valid JSON:
        {{
            "name": "value or null",
            "phone": "value or null",
            "email": "value or null",
            "property_type": "value or null",
            "location": "value or null",
            "size": "value or null",
            "budget": "value or null",
            "timeline": "value or null",
            "purpose": "value or null",
            "bedrooms": "value or null"
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse JSON response
            json_str = response.choices[0].message.content
            # Clean up if there's any extra text
            json_str = json_str.replace('```json', '').replace('```', '').strip()
            data = json.loads(json_str)
            
            # Remove null values
            return {k: v for k, v in data.items() if v and v != "null"}
            
        except Exception as e:
            print(f"Extraction Error: {e}")
            return {}