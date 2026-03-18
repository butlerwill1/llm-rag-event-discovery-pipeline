"""
Module for interacting with OpenAI's Responses API with agentic search
"""
import openai
from typing import List, Dict, Any
from config import OPENAI_API_KEY, MODEL_NAME, REASONING_EFFORT, PROMPT_TEMPLATE


class EventSearchClient:
    """
    Client for searching events using OpenAI's Responses API with web_search_preview tool.
    """
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    def search_events(self, query: str) -> str:
        """
        Search for events using OpenAI's Responses API with web search.

        Args:
            query (str): Search query for events

        Returns:
            str: Raw response content from OpenAI
        """
        try:
            # Get today's date
            from datetime import datetime
            today_date = datetime.now().strftime("%Y-%m-%d")

            # Format the prompt with the query and today's date
            formatted_prompt = PROMPT_TEMPLATE.format(query=query, today_date=today_date)

            print(f"Searching for events with query: '{query}'")
            print(f"Using agentic search with {MODEL_NAME} (reasoning effort: {REASONING_EFFORT})")

            # Create the response using OpenAI's Responses API with agentic search
            # Using a reasoning model (gpt-5) that can actively manage the search process
            response = self.client.responses.create(
                model=MODEL_NAME,
                input=formatted_prompt,
                reasoning={
                    "effort": REASONING_EFFORT  # Controls depth and latency of search
                },
                tools=[
                    {
                        "type": "web_search",
                        "search_context_size": "high",  # Get more detailed context for better event info
                        "user_location": {
                            "type": "approximate",
                            "country": "GB",
                            "city": "London",
                            "region": "London"
                        }
                    }
                ]
            )

            # Extract the response content from the Responses API format
            if hasattr(response, 'output_text') and response.output_text:
                content = response.output_text
                print(f"Received response from OpenAI (length: {len(content)} chars)")
                return content
            elif hasattr(response, 'output') and response.output:
                # Handle different response formats
                for item in response.output:
                    if item.type == "message" and hasattr(item, 'content'):
                        for content_item in item.content:
                            if content_item.type == "output_text":
                                content = content_item.text
                                print(f"Received response from OpenAI (length: {len(content)} chars)")
                                return content

            print("No response content received from OpenAI")
            return ""

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return ""
    
    def search_multiple_queries(self, queries: List[str]) -> List[str]:
        """
        Search for events using multiple queries.
        
        Args:
            queries (List[str]): List of search queries
            
        Returns:
            List[str]: List of response contents
        """
        responses = []
        
        for i, query in enumerate(queries, 1):
            print(f"\nProcessing query {i}/{len(queries)}: {query}")
            
            try:
                response = self.search_events(query)
                if response:
                    responses.append(response)
                else:
                    print(f"No response for query: {query}")
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
                continue
        
        return responses
    
    def test_connection(self) -> bool:
        """
        Test the connection to OpenAI API.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Simple test call using Responses API
            response = self.client.responses.create(
                model=MODEL_NAME,
                input="Hello, this is a test. Please respond with 'Connection successful'."
            )

            # Check for response content
            if hasattr(response, 'output_text') and response.output_text:
                content = response.output_text
                print(f"Test response: {content}")
                return "successful" in content.lower()
            elif hasattr(response, 'output') and response.output:
                # Handle different response formats
                for item in response.output:
                    if item.type == "message" and hasattr(item, 'content'):
                        for content_item in item.content:
                            if content_item.type == "output_text":
                                content = content_item.text
                                print(f"Test response: {content}")
                                return "successful" in content.lower()

            return False

        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


if __name__ == "__main__":
    # Test the client
    client = EventSearchClient()
    
    # Test connection
    print("Testing OpenAI connection...")
    if client.test_connection():
        print("✓ Connection successful!")
        
        # Test event search
        print("\nTesting event search...")
        test_query = "London tech meetup December 2024"
        response = client.search_events(test_query)
        
        if response:
            print(f"✓ Event search successful!")
            print(f"Response preview: {response[:200]}...")
        else:
            print("✗ Event search failed")
    else:
        print("✗ Connection failed")
