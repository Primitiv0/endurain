"""Email message builders for password reset notifications."""

import html

import core.apprise as core_apprise
import core.email_templates as core_email_templates


def get_password_reset_email_en(
    user_name: str, reset_link: str, email_service: core_apprise.AppriseService
) -> tuple[str, str, str]:
    """
    Build an English password reset email.

    Args:
        user_name: The recipient's display name.
        reset_link: The URL for resetting the password.
        email_service: AppriseService for footer metadata.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(user_name)
    subject = "Endurain - Password reset"
    html_content = (
        core_email_templates.html_header(subject, "Password reset request")
        + f"""
            <p>Hi {safe_name},</p>

            <p>You requested to reset your password for your Endurain account. Click the button below to reset your
                password:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: {core_email_templates.LINK_COLOR_PRIMARY}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
            </div>

            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Security notice:</strong> This link will expire in 1 hour for security reasons.
            </div>

            <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            </p>

            <p>If the button above doesn't work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: {core_email_templates.LINK_COLOR_PRIMARY};">{reset_link}</p>"""
        + core_email_templates.html_footer(
            email_service.frontend_host, core_email_templates.LINK_COLOR_PRIMARY
        )
    )

    # Create text version
    text_content = f"""
    Hi {user_name},

    You requested to reset your password for your Endurain account.

    Please click the following link to reset your password:
    {reset_link}

    This link will expire in 1 hour for security reasons.

    If you didn't request this password reset, please ignore this email. Your password will remain unchanged.

    Best regards,
    The Endurain team
    """.strip()

    return subject, html_content, text_content
