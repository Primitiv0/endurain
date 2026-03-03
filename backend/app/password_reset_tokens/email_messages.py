"""Email message builders for password reset notifications."""

import core.apprise as core_apprise


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
    subject = "Endurain - Password reset"
    html_content = f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>

<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
    <div style="background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 34px; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <img src="https://github.com/endurain-project/endurain/blob/0e17fafe450b66eda7982311e6f94cee44316684/frontend/app/public/logo/logo.svg?raw=true"
                    alt="Endurain logo" style="height: 32px; width: auto;">
                <span>Endurain</span>
            </div>
            <h3 style="margin: 0;">Password reset request</h3>
        </div>

        <div style="margin-bottom: 30px;">
            <p>Hi {user_name},</p>

            <p>You requested to reset your password for your Endurain account. Click the button below to reset your
                password:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #0d6efd; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
            </div>

            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Security notice:</strong> This link will expire in 1 hour for security reasons.
            </div>

            <p>If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            </p>

            <p>If the button above doesn't work, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; color: #0d6efd;">{reset_link}</p>
        </div>

        <div style="text-align: center; font-size: 12px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p>Best regards,<br>The Endurain team</p>
            <p>Visit Endurain at: <a style="color: #0d6efd;" href="{email_service.frontend_host}">{email_service.frontend_host}</a> -
                Source code at: <a style="color: #0d6efd;"
                    href="https://github.com/endurain-project/endurain">GitHub</a></p>
        </div>
    </div>
</body>

</html>
    """.strip()

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
