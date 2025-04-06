from typing import Dict, List, Optional, Union, Any
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import requests
from twilio.rest import Client
import firebase_admin
from firebase_admin import credentials, messaging

from .base_notification import BaseNotification, NotificationPriority, NotificationType, DeliveryMethod

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications through various delivery methods."""
    
    def __init__(self):
        """Initialize the notification service."""
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', 'notifications@auctionintelligence.com')
        
        # SendGrid configuration
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.sendgrid_from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'notifications@auctionintelligence.com')
        
        # Twilio configuration
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_from_number = os.environ.get('TWILIO_FROM_NUMBER')
        
        # Firebase configuration
        self.firebase_credentials_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
        
        # Initialize Firebase if credentials are provided
        if self.firebase_credentials_path and os.path.exists(self.firebase_credentials_path):
            try:
                cred = credentials.Certificate(self.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
        
        # Initialize Twilio client if credentials are provided
        if self.twilio_account_sid and self.twilio_auth_token:
            try:
                self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.twilio_client = None
        else:
            self.twilio_client = None
    
    def send_notification(self, notification: BaseNotification) -> bool:
        """Send a notification through all specified delivery methods.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if all delivery methods succeeded, False otherwise
        """
        success = True
        
        for method in notification.delivery_methods:
            try:
                if method == DeliveryMethod.EMAIL:
                    if self.sendgrid_api_key:
                        method_success = self._send_email_sendgrid(notification)
                    else:
                        method_success = self._send_email_smtp(notification)
                elif method == DeliveryMethod.SMS:
                    method_success = self._send_sms(notification)
                elif method == DeliveryMethod.PUSH:
                    method_success = self._send_push(notification)
                elif method == DeliveryMethod.TOAST:
                    # Toast notifications are handled by the frontend
                    method_success = True
                else:
                    logger.error(f"Unsupported delivery method: {method}")
                    method_success = False
                
                if method_success:
                    notification.mark_delivered(method)
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Failed to send notification via {method}: {e}")
                success = False
        
        return success
    
    def _send_email_smtp(self, notification: BaseNotification) -> bool:
        """Send email notification via SMTP.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Get recipient email from data or use a default
            recipient_email = notification.data.get('email')
            if not recipient_email:
                logger.error("Recipient email not provided in notification data")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient_email
            msg['Subject'] = notification.title
            
            # Add priority header
            if notification.priority == NotificationPriority.CRITICAL:
                msg['X-Priority'] = '1 (Highest)'
            elif notification.priority == NotificationPriority.HIGH:
                msg['X-Priority'] = '2 (High)'
            elif notification.priority == NotificationPriority.MEDIUM:
                msg['X-Priority'] = '3 (Normal)'
            else:
                msg['X-Priority'] = '4 (Low)'
            
            # Create HTML content
            html_content = self._create_email_html(notification)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False
    
    def _send_email_sendgrid(self, notification: BaseNotification) -> bool:
        """Send email notification via SendGrid.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.sendgrid_api_key:
                logger.error("SendGrid API key not configured")
                return False
            
            # Get recipient email from data or use a default
            recipient_email = notification.data.get('email')
            if not recipient_email:
                logger.error("Recipient email not provided in notification data")
                return False
            
            # Create email content
            html_content = self._create_email_html(notification)
            
            # Prepare SendGrid API request
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "personalizations": [
                    {
                        "to": [{"email": recipient_email}],
                        "subject": notification.title
                    }
                ],
                "from": {"email": self.sendgrid_from_email},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }
            
            # Send request
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 202:
                logger.info(f"SendGrid email sent successfully to {recipient_email}")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False
    
    def _send_sms(self, notification: BaseNotification) -> bool:
        """Send SMS notification via Twilio.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.twilio_client:
                logger.error("Twilio client not initialized")
                return False
            
            # Get recipient phone number from data
            recipient_phone = notification.data.get('phone')
            if not recipient_phone:
                logger.error("Recipient phone number not provided in notification data")
                return False
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=notification.message,
                from_=self.twilio_from_number,
                to=recipient_phone
            )
            
            logger.info(f"SMS sent successfully to {recipient_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def _send_push(self, notification: BaseNotification) -> bool:
        """Send push notification via Firebase.
        
        Args:
            notification: Notification to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if Firebase is initialized
            if not firebase_admin._apps:
                logger.error("Firebase not initialized")
                return False
            
            # Get recipient FCM token from data
            fcm_token = notification.data.get('fcm_token')
            if not fcm_token:
                logger.error("Recipient FCM token not provided in notification data")
                return False
            
            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.message
                ),
                data={
                    'notification_type': notification.notification_type.value,
                    'priority': str(notification.priority.value),
                    'data': json.dumps(notification.data)
                },
                token=fcm_token
            )
            
            # Send message
            response = messaging.send(message)
            
            logger.info(f"Push notification sent successfully, message ID: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False
    
    def _create_email_html(self, notification: BaseNotification) -> str:
        """Create HTML content for email notifications.
        
        Args:
            notification: Notification to create HTML for
            
        Returns:
            HTML content
        """
        # Priority color
        priority_colors = {
            NotificationPriority.CRITICAL: '#FF0000',  # Red
            NotificationPriority.HIGH: '#FF9900',      # Orange
            NotificationPriority.MEDIUM: '#0099FF',    # Blue
            NotificationPriority.LOW: '#999999'        # Gray
        }
        
        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{notification.title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {priority_colors.get(notification.priority, '#0099FF')};
                    color: white;
                    padding: 15px;
                    border-radius: 5px 5px 0 0;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                }}
                .button {{
                    display: inline-block;
                    background-color: {priority_colors.get(notification.priority, '#0099FF')};
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{notification.title}</h2>
            </div>
            <div class="content">
                <p>{notification.message}</p>
        """
        
        # Add action button if URL is provided
        if 'action_url' in notification.data:
            html += f"""
                <div style="text-align: center;">
                    <a href="{notification.data['action_url']}" class="button">View Details</a>
                </div>
            """
        
        # Add additional data if available
        if notification.data and len(notification.data) > 1:  # More than just action_url
            html += """
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <h3>Additional Information</h3>
                    <ul>
            """
            
            for key, value in notification.data.items():
                if key != 'action_url' and key != 'email' and key != 'phone' and key != 'fcm_token':
                    html += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
            
            html += """
                    </ul>
                </div>
            """
        
        # Add footer
        html += f"""
            </div>
            <div class="footer">
                <p>This is an automated message from Auction Intelligence. Please do not reply to this email.</p>
                <p>Sent at {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html 