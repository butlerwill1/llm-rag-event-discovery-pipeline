"""
RAG (Retrieval-Augmented Generation) for intelligent event queries.
"""

import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from .weaviate_client import WeaviateEventStore
import logging

logger = logging.getLogger(__name__)


class EventRAG:
    """RAG system for answering questions about events."""
    
    def __init__(self, weaviate_store: WeaviateEventStore = None):
        """
        Initialize RAG system.
        
        Args:
            weaviate_store: WeaviateEventStore instance (creates new if None)
        """
        self.store = weaviate_store or WeaviateEventStore()
        self.llm = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o"),
            temperature=0.3
        )
        
        # RAG prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert event analyst for London tech events.
            
                You have access to a database of events found by an AI agent. Your job is to answer 
                questions about these events by analyzing the provided context.

                Be specific and cite event names, dates, and details when answering.
                If you don't have enough information, say so clearly.
                Focus on actionable insights and trends."""),
                            ("user", """Based on these events:

                {context}

                Question: {question}

                Answer:""")
        ])
    
    def query(self, question: str, max_events: int = 20) -> str:
        """
        Answer a question about events using RAG.
        
        Args:
            question: Natural language question
            max_events: Maximum number of events to retrieve for context
            
        Returns:
            Answer string
        """
        logger.info(f"RAG query: {question}")
        
        # 1. Retrieve relevant events from Weaviate
        events = self.store.search_events(question, limit=max_events)
        
        if not events:
            return "I don't have any events in the database yet. Please run the event finder first."
        
        # 2. Build context from retrieved events
        context = self._build_context(events)
        
        # 3. Generate answer using LLM
        messages = self.prompt.format_messages(
            context=context,
            question=question
        )
        
        response = self.llm.invoke(messages)
        
        logger.info(f"RAG answer generated (used {len(events)} events)")
        
        return response.content
    
    def _build_context(self, events: List[Dict[str, Any]]) -> str:
        """Build context string from events."""
        context_parts = []
        
        for i, event in enumerate(events, 1):
            parts = [f"{i}. {event.get('event_name', 'Unknown Event')}"]
            
            if event.get('event_date'):
                parts.append(f"   Date: {event['event_date']}")
            
            if event.get('event_type'):
                parts.append(f"   Type: {event['event_type']}")
            
            if event.get('venue'):
                parts.append(f"   Venue: {event['venue']}")
            
            if event.get('ticket_price'):
                parts.append(f"   Price: {event['ticket_price']}")
            
            if event.get('description'):
                # Truncate long descriptions
                desc = event['description']
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                parts.append(f"   Description: {desc}")
            
            if event.get('speakers'):
                parts.append(f"   Speakers: {event['speakers']}")
            
            context_parts.append("\n".join(parts))
        
        return "\n\n".join(context_parts)
    
    def get_trends_summary(self) -> str:
        """Generate a summary of trending topics in events."""
        return self.query(
            "What are the main trending topics and themes across all events? "
            "Group by topic and provide counts."
        )
    
    def find_free_events(self) -> str:
        """Find free or low-cost events."""
        return self.query(
            "What free or low-cost events are available? "
            "List them with dates and venues."
        )
    
    def compare_event_types(self) -> str:
        """Compare different types of events."""
        return self.query(
            "Compare the different types of events (hackathons, workshops, conferences, etc.). "
            "How many of each type are there and what are the key differences?"
        )
    
    def upcoming_this_month(self) -> str:
        """Get events happening this month."""
        return self.query(
            "What events are happening this month? "
            "List them chronologically with key details."
        )


def main():
    """Example usage of RAG system."""
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize RAG
    rag = EventRAG()
    
    # Check if we have events
    count = rag.store.get_event_count()
    print(f"\n📊 Total events in database: {count}\n")
    
    if count == 0:
        print("⚠️  No events found. Run main.py first to populate the database.")
        return
    
    # Interactive mode or single query
    if len(sys.argv) > 1:
        # Single query from command line
        question = " ".join(sys.argv[1:])
        print(f"❓ Question: {question}\n")
        answer = rag.query(question)
        print(f"💡 Answer:\n{answer}\n")
    else:
        # Interactive mode
        print("🤖 Event RAG System - Ask questions about London events!")
        print("   Type 'quit' to exit\n")
        
        while True:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            print()
            answer = rag.query(question)
            print(f"💡 Answer:\n{answer}\n")


if __name__ == "__main__":
    main()
