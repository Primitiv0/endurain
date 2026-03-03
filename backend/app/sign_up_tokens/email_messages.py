"""Email message builders for sign-up notifications."""

import html

import core.apprise as core_apprise
import core.email_templates as core_email_templates


def get_signup_confirmation_email_en(
    user_name: str, signup_link: str, email_service: core_apprise.AppriseService
) -> tuple[str, str, str]:
    """
    Return the subject, HTML body, and plain-text body for an English sign-up
    confirmation email.

    Args:
        user_name (str): The recipient's display name inserted into the
            greeting.
        signup_link (str): The URL the user will follow to confirm their
            sign-up; inserted into the CTA button and included as a plain link
            for clients that do not render the button.
        email_service (core_apprise.AppriseService): Notification service
            instance used to obtain service metadata (e.g., `frontend_host`)
            for the email footer.

    Returns:
        tuple[str, str, str]: A 3-tuple containing:
            - subject: The email subject line.
            - html_content: The full HTML email content (string) including
                inline styles, logo, a prominent "Confirm Account" button
                linking to `signup_link`, a security notice about a 24-hour
                expiry, and a footer referencing `email_service.frontend_host`.
            - text_content: A plain-text alternative suitable for clients that
                do not render HTML, containing the greeting, confirmation
                instructions, the raw `signup_link`, expiry notice, and
                sign-off.

    Notes:
        - The function only constructs and returns strings; it does not send
            emails or perform network I/O.
        - Calling code should ensure `signup_link` and `user_name` are properly
            validated/sanitized as needed.
        - The HTML is crafted with inline styles for broad email-client
            compatibility.
    """
    safe_name = html.escape(user_name)
    subject = "Endurain - Confirm your account"
    html_content = (
        core_email_templates.html_header(subject, "Confirm your account")
        + f"""
            <p>Hi {safe_name},</p>

            <p>Thank you for signing up for Endurain! Please confirm your account by clicking the button below:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{signup_link}" style="background-color: #198754; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Confirm Account</a>
            </div>

            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Security notice:</strong> This confirmation link will expire in 24 hours.
            </div>

            <p>If you didn’t create an Endurain account, please ignore this email.</p>

            <p>If the button above doesn’t work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: {core_email_templates.LINK_COLOR_SUCCESS};">{signup_link}</p>"""
        + core_email_templates.html_footer(
            email_service.frontend_host, core_email_templates.LINK_COLOR_SUCCESS
        )
    )

    # Create text version
    text_content = f"""
    Hi {user_name},

    Thank you for signing up for Endurain!

    Please confirm your account by clicking the following link:
    {signup_link}

    This confirmation link will expire in 24 hours.

    If you didn’t create an Endurain account, please ignore this email.

    Best regards,
    The Endurain team
    """.strip()

    return subject, html_content, text_content


def get_admin_signup_notification_email_en(
    user_name: str,
    sign_up_user_name: str,
    sign_up_user_username: str,
    email_service: core_apprise.AppriseService,
) -> tuple[str, str, str]:
    """
    Build an English admin notification email for a pending sign-up.

    Args:
        user_name: Display name of the admin receiving the notification.
        sign_up_user_name: Display name of the user who signed up.
        sign_up_user_username: Username of the user who signed up, used to
            build the direct link to the admin approval page.
        email_service: AppriseService for footer metadata.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(user_name)
    safe_sign_up_name = html.escape(sign_up_user_name)
    safe_sign_up_username = html.escape(sign_up_user_username)
    subject = "Endurain - New user sign-up pending approval"
    html_content = (
        core_email_templates.html_header(subject, "New sign-up requires approval")
        + f"""
            <p>Hello {safe_name},</p>

            <p>A new user has signed up and is awaiting approval:</p>

            <div style="background-color: #e9ecef; border: 1px solid #ccc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>User:</strong> {safe_sign_up_name}
            </div>

            <p>Please log in to the Endurain admin panel to review and approve this request.</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{email_service.frontend_host}/settings?tab=users&username={safe_sign_up_username}" style="background-color: {core_email_templates.LINK_COLOR_SUCCESS}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Go to Admin Panel</a>
            </div>

            <p>If the button above doesn't work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: {core_email_templates.LINK_COLOR_SUCCESS};">{email_service.frontend_host}/settings?tab=users&username={safe_sign_up_username}</p>"""
        + core_email_templates.html_footer(
            email_service.frontend_host,
            core_email_templates.LINK_COLOR_SUCCESS,
            sign_off="The Endurain system",
        )
    )

    text_content = f"""
    Hello {user_name},

    A new user has signed up and is awaiting approval.

    User: {sign_up_user_name}

    Please log in to the Endurain admin panel to review and approve this request:
    {email_service.frontend_host}/settings?tab=users&username={safe_sign_up_username}

    Best regards,
    The Endurain system
    """.strip()

    return subject, html_content, text_content


def get_user_signup_approved_email_en(
    sign_up_user_name: str,
    sign_up_user_username: str,
    email_service: core_apprise.AppriseService,
) -> tuple[str, str, str]:
    """
    Build an English account-approved notification email for a newly approved
    user.

    Args:
        sign_up_user_name: Display name of the approved user.
        sign_up_user_username: Username of the approved user, shown in the
            email body.
        email_service: AppriseService for footer metadata.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(sign_up_user_name)
    safe_username = html.escape(sign_up_user_username)
    subject = "Endurain - Your account has been approved"
    html_content = (
        core_email_templates.html_header(subject, "Your account is now active")
        + f"""
            <p>Hello {safe_name},</p>

            <p>Good news! Your account has been approved and is now active.</p>

            <div style="background-color: #e9ecef; border: 1px solid #ccc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Username:</strong> {safe_username}
            </div>

            <p>You can now log in and start using Endurain:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{email_service.frontend_host}/login" style="background-color: {core_email_templates.LINK_COLOR_SUCCESS}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Log in to Endurain</a>
            </div>

            <p>If the button above doesn’t work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: {core_email_templates.LINK_COLOR_SUCCESS};">{email_service.frontend_host}/login</p>"""
        + core_email_templates.html_footer(
            email_service.frontend_host, core_email_templates.LINK_COLOR_SUCCESS
        )
    )

    text_content = f"""
    Hello {sign_up_user_name},

    Good news! Your account has been approved and is now active.

    Username: {sign_up_user_username}

    You can now log in and start using Endurain:
    {email_service.frontend_host}/login

    Best regards,
    The Endurain team
    """.strip()

    return subject, html_content, text_content
