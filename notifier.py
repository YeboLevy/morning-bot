#!/usr/bin/env python3
# ============================================================
# notifier.py — Universal Notification Manager
#
# WHAT THIS IS:
# A unified notification system that can send alerts via
# multiple methods: macOS notifications, email, or both.
#
# WHY THIS IS USEFUL:
# Instead of writing notification code in every bot, you
# write it once here and reuse it everywhere.
#
# USAGE:
#   from notifier import Notifier
#
#   notifier = Notifier()
#   notifier.send("Hello", "This is a test", method="desktop")
#   notifier.send("Alert", "Check this!", method="email")
#   notifier.send("Important", "Urgent!", method="all")
#
# SECURITY:
# - Email credentials stored in .env file (never in code!)
# - .env file is gitignored (never committed to GitHub)
# - Uses app-specific passwords (not your real password)
#
# ============================================================

import os
import sys
import smtplib
import subprocess
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# LOGGING SETUP
# All notifications are logged for audit trail
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('notifications.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ============================================================
# NOTIFIER CLASS
# ============================================================

class Notifier:
    """
    Universal notification manager with multiple delivery methods.

    NOTIFICATION METHODS:
    - desktop: macOS native notifications (instant, no setup)
    - email: Send HTML emails with attachments
    - all: Try both methods

    URGENCY LEVELS:
    - info: Normal notification (green)
    - warning: Needs attention (yellow)
    - error: Critical alert (red)

    ERROR HANDLING:
    If one method fails, tries the next (graceful degradation)
    All failures are logged but don't crash the bot
    """

    def __init__(self):
        """
        Initialize the notifier and load email credentials.

        EMAIL CREDENTIALS:
        Read from .env file using os.getenv()
        Never hardcode passwords in your code!

        .env file format:
        EMAIL_USER=your.email@gmail.com
        EMAIL_PASSWORD=your_app_specific_password
        EMAIL_TO=recipient@example.com
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        """
        # Email configuration from environment variables
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to = os.getenv('EMAIL_TO', self.email_user)  # Default: send to self
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

        # Check if email is configured
        self.email_available = bool(self.email_user and self.email_password)

        if not self.email_available:
            logger.warning("Email not configured (missing EMAIL_USER or EMAIL_PASSWORD)")

    # ============================================================
    # PUBLIC API
    # ============================================================

    def send(self, title, message, method="desktop", urgency="info", attachment=None):
        """
        Send a notification via the specified method.

        PARAMETERS:
        - title: Notification title (short, 1-10 words)
        - message: Notification body (can be longer)
        - method: "desktop", "email", or "all"
        - urgency: "info", "warning", or "error"
        - attachment: Path to file to attach (email only)

        RETURNS:
        - True if at least one method succeeded
        - False if all methods failed

        EXAMPLES:
        # Simple desktop notification
        notifier.send("Task Complete", "Your report is ready")

        # Email with attachment
        notifier.send(
            "Daily Report",
            "See attached briefing",
            method="email",
            attachment="briefing.txt"
        )

        # Critical alert via all methods
        notifier.send(
            "Error!",
            "Backup failed",
            method="all",
            urgency="error"
        )
        """
        # Add emoji based on urgency
        icon = self._get_icon(urgency)
        title_with_icon = f"{icon} {title}"

        # Log the notification
        logger.info(f"Sending notification: {title} ({method}, {urgency})")

        # Track which methods succeeded
        success = False

        # Try the requested method(s)
        if method == "desktop" or method == "all":
            if self._send_desktop(title_with_icon, message):
                success = True

        if method == "email" or method == "all":
            if self._send_email(title_with_icon, message, urgency, attachment):
                success = True

        if not success:
            logger.error(f"All notification methods failed for: {title}")

        return success

    # ============================================================
    # DESKTOP NOTIFICATIONS (macOS)
    # ============================================================

    def _send_desktop(self, title, message):
        """
        Send a macOS desktop notification using osascript.

        macOS NOTIFICATIONS EXPLAINED:
        osascript is Apple's command-line tool for running AppleScript.
        AppleScript is a scripting language built into macOS.

        The command we run:
        osascript -e 'display notification "message" with title "title"'

        BREAKDOWN:
        - osascript: Run AppleScript from command line
        - -e: Execute the following script
        - display notification: AppleScript command to show notification
        - with title: Set the notification title

        NOTIFICATION BEHAVIOR:
        - Appears as banner in top-right corner
        - Plays default notification sound
        - Disappears after ~5 seconds
        - Stored in Notification Center for 24 hours

        CROSS-PLATFORM:
        - macOS: Use osascript (this method)
        - Linux: Use notify-send
        - Windows: Use win10toast library

        RETURNS:
        - True if notification sent successfully
        - False if failed (osascript not available, permissions issue)
        """
        try:
            # Escape quotes in title and message
            # If title is: Say "Hello"
            # We need: Say \\"Hello\\"
            title_escaped = title.replace('"', '\\"')
            message_escaped = message.replace('"', '\\"')

            # Build the AppleScript command
            # Example output:
            # display notification "Task complete" with title "✅ Success"
            script = f'display notification "{message_escaped}" with title "{title_escaped}"'

            # Execute the command
            # subprocess.run() executes a shell command from Python
            # ['osascript', '-e', script] = osascript -e 'display notification...'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,  # Capture stdout/stderr
                text=True,            # Return strings (not bytes)
                check=False           # Don't raise exception on error
            )

            if result.returncode == 0:
                logger.debug(f"Desktop notification sent: {title}")
                return True
            else:
                logger.warning(f"Desktop notification failed: {result.stderr}")
                return False

        except FileNotFoundError:
            # osascript not found (not on macOS or not in PATH)
            logger.warning("Desktop notifications not available (osascript not found)")
            return False

        except Exception as e:
            logger.error(f"Desktop notification error: {e}")
            return False

    # ============================================================
    # EMAIL NOTIFICATIONS
    # ============================================================

    def _send_email(self, title, message, urgency, attachment=None):
        """
        Send an email notification with optional HTML formatting.

        EMAIL SENDING PROCESS:
        1. Create message (plain text + HTML version)
        2. Add attachment if provided
        3. Connect to SMTP server
        4. Start TLS encryption (secure connection)
        5. Login with credentials
        6. Send message
        7. Disconnect

        SMTP EXPLAINED:
        SMTP = Simple Mail Transfer Protocol
        It's how email clients send mail to mail servers

        SMTP SERVERS:
        - Gmail: smtp.gmail.com port 587
        - Outlook: smtp-mail.outlook.com port 587
        - Yahoo: smtp.mail.yahoo.com port 587

        TLS ENCRYPTION:
        - Port 587 uses STARTTLS (start with unencrypted, upgrade to TLS)
        - Port 465 uses SSL (encrypted from the start)
        - Never use port 25 (unencrypted, often blocked)

        APP PASSWORDS:
        Gmail/Outlook require "app-specific passwords", not your real password!
        This is more secure because:
        - App password only works for SMTP, not full account access
        - Can be revoked without changing your main password
        - If leaked, attacker can't access your email account

        How to create:
        - Gmail: https://myaccount.google.com/apppasswords
        - Outlook: https://account.live.com/proofs/AppPassword

        MULTIPART EMAIL:
        We send both plain text and HTML versions
        Email client shows HTML if supported, plain text otherwise
        This ensures maximum compatibility

        RETURNS:
        - True if email sent successfully
        - False if failed (no credentials, network error, auth error)
        """
        # Check if email is configured
        if not self.email_available:
            logger.debug("Email skipped (not configured)")
            return False

        try:
            # ══════════════════════════════════════════════════
            # STEP 1: Create the email message
            # ══════════════════════════════════════════════════

            # MIMEMultipart allows us to send both plain text and HTML
            # MIME = Multipurpose Internet Mail Extensions
            msg = MIMEMultipart('alternative')  # 'alternative' = try HTML, fallback to plain text

            msg['From'] = self.email_user
            msg['To'] = self.email_to
            msg['Subject'] = title

            # ══════════════════════════════════════════════════
            # STEP 2: Create plain text and HTML versions
            # ══════════════════════════════════════════════════

            # Plain text version (always works)
            text_body = f"{title}\n\n{message}\n\n---\nSent by Notifier Bot"

            # HTML version (pretty formatting)
            # Uses inline CSS because email clients don't support external stylesheets
            html_body = f"""
            <html>
              <head></head>
              <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                  <h2 style="color: {self._get_color(urgency)}; margin-top: 0;">
                    {title}
                  </h2>
                  <p style="font-size: 16px; line-height: 1.6; color: #333;">
                    {message.replace(chr(10), '<br>')}
                  </p>
                  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                  <p style="font-size: 12px; color: #999;">
                    Sent by Notifier Bot on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                  </p>
                </div>
              </body>
            </html>
            """

            # Attach both versions
            # Email client will choose which one to display
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # ══════════════════════════════════════════════════
            # STEP 3: Add attachment if provided
            # ══════════════════════════════════════════════════

            if attachment and Path(attachment).exists():
                self._attach_file(msg, attachment)

            # ══════════════════════════════════════════════════
            # STEP 4: Connect to SMTP server and send
            # ══════════════════════════════════════════════════

            # Create SMTP connection
            # SMTP() doesn't connect yet, just creates the object
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                # Enable debug output (helpful for troubleshooting)
                # server.set_debuglevel(1)  # Uncomment to see SMTP conversation

                # Start TLS encryption
                # This upgrades the connection from unencrypted to encrypted
                # STARTTLS HANDSHAKE:
                # 1. Client: "STARTTLS"
                # 2. Server: "220 Ready to start TLS"
                # 3. Client & Server: Perform TLS handshake
                # 4. Connection is now encrypted
                server.starttls()

                # Login with credentials
                # This sends: AUTH LOGIN <base64_username> <base64_password>
                # Server responds with 235 Authentication successful
                server.login(self.email_user, self.email_password)

                # Send the message
                # .as_string() converts MIMEMultipart to RFC 822 format
                # RFC 822 = Internet Message Format standard
                server.send_message(msg)

            logger.info(f"Email sent to {self.email_to}: {title}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            # Wrong username/password or app password not enabled
            logger.error(f"Email authentication failed: {e}")
            logger.error("Hint: Gmail requires an app-specific password")
            return False

        except smtplib.SMTPException as e:
            # SMTP protocol error (server rejected message, etc.)
            logger.error(f"SMTP error: {e}")
            return False

        except Exception as e:
            # Network error, timeout, etc.
            logger.error(f"Email send error: {e}")
            return False

    def _attach_file(self, msg, filepath):
        """
        Attach a file to an email message.

        FILE ATTACHMENT EXPLAINED:
        Email attachments use MIME (Multipurpose Internet Mail Extensions)

        PROCESS:
        1. Read file as binary data
        2. Encode in base64 (converts binary to text)
        3. Add MIME headers (filename, content type)
        4. Attach to message

        Why base64?
        Email was designed for text, not binary data.
        Base64 converts any file (image, PDF, etc.) into text that
        can be safely transmitted via email.

        Example:
        Binary: 10010110 11001010
        Base64: lso=

        MIME TYPES:
        application/octet-stream = generic binary file
        Could be more specific:
        - text/plain for .txt
        - image/png for .png
        - application/pdf for .pdf

        But octet-stream works for everything!
        """
        try:
            filepath = Path(filepath)
            filename = filepath.name

            # Read file in binary mode
            with open(filepath, 'rb') as f:
                file_data = f.read()

            # Create MIME attachment
            # MIMEBase = base class for non-text MIME parts
            # 'application' = MIME main type
            # 'octet-stream' = MIME subtype (generic binary)
            part = MIMEBase('application', 'octet-stream')

            # Set the payload (file contents)
            part.set_payload(file_data)

            # Encode in base64
            # This converts binary data to ASCII text
            # Required because email is text-based
            encoders.encode_base64(part)

            # Add header with filename
            # Content-Disposition: attachment tells email client
            # this is an attachment (not inline content)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            # Attach to message
            msg.attach(part)

            logger.debug(f"Attached file: {filename}")

        except Exception as e:
            logger.warning(f"Could not attach file {filepath}: {e}")

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def _get_icon(self, urgency):
        """
        Get emoji icon based on urgency level.

        VISUAL INDICATORS:
        Emojis make notifications instantly scannable
        Your eyes recognize ❌ as error before reading the text!

        Color psychology:
        - Green (✅) = Success, safe, go
        - Yellow (⚠️) = Caution, attention needed
        - Red (❌) = Danger, error, stop
        """
        icons = {
            'info': '✅',      # Success/completed
            'warning': '⚠️',   # Needs attention
            'error': '❌',     # Critical error
        }
        return icons.get(urgency, 'ℹ️')  # Default: info icon

    def _get_color(self, urgency):
        """
        Get HTML color based on urgency level.

        Used in HTML emails for colored titles

        COLORS:
        - #28a745 = Green (success)
        - #ffc107 = Yellow (warning)
        - #dc3545 = Red (error)

        These match Bootstrap's alert colors (industry standard)
        """
        colors = {
            'info': '#28a745',      # Green
            'warning': '#ffc107',   # Yellow
            'error': '#dc3545',     # Red
        }
        return colors.get(urgency, '#17a2b8')  # Default: blue


# ============================================================
# CONVENIENCE FUNCTIONS
# For simple one-off notifications without creating a Notifier instance
# ============================================================

def send_notification(title, message, method="desktop", urgency="info", attachment=None):
    """
    Send a notification without creating a Notifier instance.

    This is a convenience function for quick notifications.

    USAGE:
    from notifier import send_notification

    send_notification("Hello", "World")
    """
    notifier = Notifier()
    return notifier.send(title, message, method, urgency, attachment)


# ============================================================
# COMMAND-LINE INTERFACE
# Run this script directly to test notifications
# ============================================================

if __name__ == "__main__":
    """
    Test the notifier from command line.

    USAGE:
    python3 notifier.py "Title" "Message"
    python3 notifier.py "Title" "Message" --method email
    python3 notifier.py "Title" "Message" --urgency warning
    """
    if len(sys.argv) < 3:
        print("Usage: python3 notifier.py <title> <message> [--method desktop|email|all] [--urgency info|warning|error]")
        print("\nExamples:")
        print('  python3 notifier.py "Hello" "World"')
        print('  python3 notifier.py "Alert" "Check this!" --method email')
        print('  python3 notifier.py "Error" "Something broke" --urgency error --method all')
        sys.exit(1)

    # Parse command-line arguments
    title = sys.argv[1]
    message = sys.argv[2]

    # Optional arguments
    method = 'desktop'
    urgency = 'info'

    if '--method' in sys.argv:
        idx = sys.argv.index('--method')
        if idx + 1 < len(sys.argv):
            method = sys.argv[idx + 1]

    if '--urgency' in sys.argv:
        idx = sys.argv.index('--urgency')
        if idx + 1 < len(sys.argv):
            urgency = sys.argv[idx + 1]

    # Send notification
    notifier = Notifier()
    success = notifier.send(title, message, method=method, urgency=urgency)

    if success:
        print(f"✓ Notification sent successfully ({method})")
    else:
        print(f"✗ Notification failed")
        sys.exit(1)
