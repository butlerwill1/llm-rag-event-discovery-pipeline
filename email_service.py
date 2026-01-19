"""
Email service for sending event digests via AWS SES
"""
import boto3
from datetime import datetime
from typing import List, Dict, Any
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class EmailService:
    """
    Service for formatting and sending event digest emails via AWS SES.
    """
    
    def __init__(self, region_name: str, from_email: str, to_email: str):
        """
        Initialize the email service.
        
        Args:
            region_name (str): AWS region for SES (e.g., 'eu-west-1')
            from_email (str): Verified sender email address
            to_email (str): Recipient email address
        """
        self.ses_client = boto3.client('ses', region_name=region_name)
        self.from_email = from_email
        self.to_email = to_email
        self.region_name = region_name
    
    def format_events_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group events by type for organized display.
        
        Args:
            events (List[Dict[str, Any]]): List of events
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Events grouped by type
        """
        grouped = {}
        for event in events:
            event_type = event.get('event_type', 'other').upper()
            if event_type not in grouped:
                grouped[event_type] = []
            grouped[event_type].append(event)
        
        # Sort events within each type by date
        for event_type in grouped:
            grouped[event_type].sort(key=lambda x: x.get('event_date', ''))
        
        return grouped
    
    def create_text_email(self, new_events: List[Dict[str, Any]], total_events: int) -> str:
        """
        Create plain text version of the email.
        
        Args:
            new_events (List[Dict[str, Any]]): New events found this week
            total_events (int): Total events in database
            
        Returns:
            str: Plain text email content
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        
        lines = [
            f"Weekly Event Digest - {current_date}",
            "",
            "Hi,",
            "",
        ]
        
        if not new_events:
            lines.extend([
                "No new events were found this week.",
                "",
                f"Total events in database: {total_events}",
                "",
                "Powered by your Event Finding AI Agent"
            ])
            return "\n".join(lines)
        
        lines.append(f"Here are your London events for this week ({len(new_events)} new events):")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        
        # Group events by type
        grouped_events = self.format_events_by_type(new_events)
        
        event_number = 1
        for event_type, events in grouped_events.items():
            # Type header with emoji
            type_emoji = self._get_type_emoji(event_type)
            lines.append(f"{type_emoji} {event_type.upper()} ({len(events)} event{'s' if len(events) > 1 else ''})")
            lines.append("")
            
            for event in events:
                lines.append(f"{event_number}. {event['event_name']}")
                lines.append(f"   Date: {event['event_date']}")
                lines.append(f"   Price: {event.get('ticket_price', 'N/A')}")
                lines.append(f"   Venue: {event.get('venue', 'N/A')}")
                
                if event.get('speakers') and event['speakers'] not in ['Speakers TBA', 'Not specified']:
                    lines.append(f"   Speakers: {event['speakers']}")
                
                if event.get('description'):
                    desc = event['description'][:200] + "..." if len(event['description']) > 200 else event['description']
                    lines.append(f"   Description: {desc}")
                
                lines.append(f"   URL: {event['event_url']}")
                lines.append("")
                event_number += 1
            
            lines.append("=" * 60)
            lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append(f"- Total new events found: {len(new_events)}")
        lines.append(f"- Total events in database: {total_events}")
        lines.append("")
        lines.append("Powered by your Event Finding AI Agent")
        
        return "\n".join(lines)
    
    def create_html_email(self, new_events: List[Dict[str, Any]], total_events: int) -> str:
        """
        Create HTML version of the email with basic formatting.
        
        Args:
            new_events (List[Dict[str, Any]]): New events found this week
            total_events (int): Total events in database
            
        Returns:
            str: HTML email content
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .event {{ background-color: #f8f9fa; padding: 15px; margin: 15px 0; border-left: 4px solid #3498db; }}
                .event-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
                .event-detail {{ margin: 5px 0; }}
                .event-detail strong {{ color: #555; }}
                .summary {{ background-color: #e8f4f8; padding: 15px; margin-top: 30px; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; font-size: 12px; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>📅 Weekly Event Digest - {current_date}</h1>
            <p>Hi,</p>
        """
        
        if not new_events:
            html += f"""
            <p>No new events were found this week.</p>
            <div class="summary">
                <strong>Total events in database:</strong> {total_events}
            </div>
            <div class="footer">
                Powered by your Event Finding AI Agent
            </div>
            </body>
            </html>
            """
            return html
        
        html += f"<p>Here are your London events for this week (<strong>{len(new_events)} new events</strong>):</p>"
        
        # Group events by type
        grouped_events = self.format_events_by_type(new_events)

        event_number = 1
        for event_type, events in grouped_events.items():
            type_emoji = self._get_type_emoji(event_type)
            html += f"<h2>{type_emoji} {event_type.upper()} ({len(events)} event{'s' if len(events) > 1 else ''})</h2>"

            for event in events:
                html += f'<div class="event">'
                html += f'<div class="event-title">{event_number}. {event["event_name"]}</div>'
                html += f'<div class="event-detail"><strong>📅 Date:</strong> {event["event_date"]}</div>'
                html += f'<div class="event-detail"><strong>💰 Price:</strong> {event.get("ticket_price", "N/A")}</div>'
                html += f'<div class="event-detail"><strong>📍 Venue:</strong> {event.get("venue", "N/A")}</div>'

                if event.get('speakers') and event['speakers'] not in ['Speakers TBA', 'Not specified']:
                    html += f'<div class="event-detail"><strong>🎤 Speakers:</strong> {event["speakers"]}</div>'

                if event.get('description'):
                    desc = event['description'][:300] + "..." if len(event['description']) > 300 else event['description']
                    html += f'<div class="event-detail"><strong>📝 Description:</strong> {desc}</div>'

                html += f'<div class="event-detail"><strong>🔗 Link:</strong> <a href="{event["event_url"]}">{event["event_url"]}</a></div>'
                html += '</div>'
                event_number += 1

        # Summary
        html += f"""
        <div class="summary">
            <strong>📊 Summary:</strong><br>
            • Total new events found: {len(new_events)}<br>
            • Total events in database: {total_events}
        </div>
        <div class="footer">
            Powered by your Event Finding AI Agent
        </div>
        </body>
        </html>
        """

        return html

    def _get_type_emoji(self, event_type: str) -> str:
        """
        Get emoji for event type.

        Args:
            event_type (str): Event type

        Returns:
            str: Emoji character
        """
        emoji_map = {
            'HACKATHON': '💻',
            'MARATHON': '🏃',
            'HALF MARATHON': '🏃',
            'HALF-MARATHON': '🏃',
            'RUN': '🏃',
            'RUNNING': '🏃',
            '10K': '🏃',
            '5K': '🏃',
            'CONFERENCE': '🎤',
            'MEETUP': '🤝',
            'NETWORKING': '🤝',
            'WORKSHOP': '🛠️',
            'SEMINAR': '📚',
            'WEBINAR': '💻',
            'TECH': '💻',
            'AI': '🤖',
            'CLIMATE': '🌍',
            'DESIGN': '🎨',
            'PRODUCT': '📦',
            'STARTUP': '🚀',
            'FINTECH': '💰',
            'WEB3': '⛓️',
            'BLOCKCHAIN': '⛓️',
            'DATA': '📊'
        }

        event_type_upper = event_type.upper()

        # Check for exact match
        if event_type_upper in emoji_map:
            return emoji_map[event_type_upper]

        # Check for partial match
        for key, emoji in emoji_map.items():
            if key in event_type_upper:
                return emoji

        return '🎯'  # Default emoji

    def send_email(self, subject: str, text_body: str, html_body: str) -> bool:
        """
        Send email via AWS SES.

        Args:
            subject (str): Email subject
            text_body (str): Plain text email body
            html_body (str): HTML email body

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={
                    'ToAddresses': [self.to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            print(f"✅ Email sent successfully!")
            print(f"   Message ID: {response['MessageId']}")
            print(f"   From: {self.from_email}")
            print(f"   To: {self.to_email}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ Failed to send email via SES:")
            print(f"   Error Code: {error_code}")
            print(f"   Error Message: {error_message}")

            if error_code == 'MessageRejected':
                print("   💡 Tip: Make sure both sender and recipient emails are verified in SES (if in sandbox mode)")
            elif error_code == 'AccessDenied':
                print("   💡 Tip: Check IAM permissions for ses:SendEmail")

            return False
        except Exception as e:
            print(f"❌ Unexpected error sending email: {e}")
            return False

    def send_weekly_digest(self, new_events: List[Dict[str, Any]], total_events: int) -> bool:
        """
        Send the weekly event digest email.

        Args:
            new_events (List[Dict[str, Any]]): New events found this week
            total_events (int): Total events in database

        Returns:
            bool: True if sent successfully, False otherwise
        """
        current_date = datetime.now().strftime("%B %d, %Y")

        if new_events:
            subject = f"📅 Weekly Event Digest - {len(new_events)} New Events - {current_date}"
        else:
            subject = f"📅 Weekly Event Digest - No New Events - {current_date}"

        # Create both text and HTML versions
        text_body = self.create_text_email(new_events, total_events)
        html_body = self.create_html_email(new_events, total_events)

        # Send the email
        return self.send_email(subject, text_body, html_body)


def create_email_service_from_env() -> EmailService:
    """
    Create EmailService instance from environment variables.

    Returns:
        EmailService: Configured email service
    """
    region = os.getenv('AWS_REGION', 'eu-west-1')
    from_email = os.getenv('SES_FROM_EMAIL')
    to_email = os.getenv('SES_TO_EMAIL', 'butler.will1@gmail.com')

    if not from_email:
        raise ValueError("SES_FROM_EMAIL environment variable is required")

    return EmailService(region, from_email, to_email)


if __name__ == "__main__":
    # Test the email service
    print("Testing Email Service...")

    # Sample test events
    test_events = [
        {
            'event_name': 'London AI Hackathon',
            'event_date': '2025-03-15',
            'event_type': 'hackathon',
            'event_url': 'https://example.com/ai-hackathon',
            'description': 'A 48-hour hackathon focused on building AI solutions for climate change with mentorship from industry experts.',
            'ticket_price': 'Free',
            'venue': 'Google Campus London, Shoreditch',
            'speakers': 'Dr. Jane Smith (DeepMind), John Doe (TechStars)'
        },
        {
            'event_name': 'Royal Parks Half Marathon',
            'event_date': '2025-10-12',
            'event_type': 'half-marathon',
            'event_url': 'https://example.com/royal-parks',
            'description': 'Scenic half marathon through London\'s beautiful royal parks.',
            'ticket_price': '£50',
            'venue': 'Hyde Park, Central London',
            'speakers': 'Not specified'
        }
    ]

    try:
        email_service = create_email_service_from_env()

        # Test email formatting
        print("\n--- Plain Text Email ---")
        text_email = email_service.create_text_email(test_events, 47)
        print(text_email)

        print("\n--- Sending Test Email ---")
        success = email_service.send_weekly_digest(test_events, 47)

        if success:
            print("\n✅ Test email sent successfully!")
        else:
            print("\n❌ Failed to send test email")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Make sure to set these environment variables:")
        print("   - SES_FROM_EMAIL (required)")
        print("   - SES_TO_EMAIL (optional, defaults to butler.will1@gmail.com)")
        print("   - AWS_REGION (optional, defaults to eu-west-1)")
    except Exception as e:
        print(f"❌ Error: {e}")
