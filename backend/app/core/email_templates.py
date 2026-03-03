"""Shared HTML email template helpers for all Endurain email builders."""

# Bootstrap-derived brand colours used across email templates.
LINK_COLOR_PRIMARY = "#0d6efd"  # blue  – password reset
LINK_COLOR_SUCCESS = "#198754"  # green – sign-up flows

_LOGO_URL = (
    "https://github.com/endurain-project/endurain/blob/"
    "0e17fafe450b66eda7982311e6f94cee44316684/"
    "frontend/app/public/logo/logo.svg?raw=true"
)


def html_header(title: str, heading: str) -> str:
    """
    Return the opening HTML block shared by all Endurain emails.

    Includes the doctype, ``<head>``, ``<body>`` wrapper, branded logo
    header with ``heading``, and the opening tag of the content
    ``<div>`` that callers must fill and then close with
    :func:`html_footer`.

    Args:
        title: Value placed in ``<title>`` (typically the email subject).
        heading: Text rendered inside the ``<h3>`` below the logo.

    Returns:
        A partial HTML string ending with an open ``<div
        style="margin-bottom: 30px;">``.
    """
    return f"""\
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>

<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
    <div style="background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="font-size: 34px; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                <img src="{_LOGO_URL}"
                    alt="Endurain logo" style="height: 32px; width: auto;">
                <span>Endurain</span>
            </div>
            <h3 style="margin: 0;">{heading}</h3>
        </div>

        <div style="margin-bottom: 30px;">"""


def html_footer(
    frontend_host: str,
    link_color: str,
    sign_off: str = "The Endurain team",
) -> str:
    """
    Return the closing HTML block shared by all Endurain emails.

    Closes the content ``<div>`` opened by :func:`html_header`, renders
    the footer with a sign-off greeting and links to the frontend host
    and the GitHub repository, then closes the outer wrapper,
    ``<body>``, and ``<html>``.

    Args:
        frontend_host: Base URL of the Endurain frontend, shown in the
            footer link (e.g. ``"https://endurain.example.com"``).
        link_color: CSS colour string applied to all footer anchor tags.
            Use module-level constants :data:`LINK_COLOR_PRIMARY` or
            :data:`LINK_COLOR_SUCCESS` for consistency.
        sign_off: Name used in the "Best regards" line.
            Defaults to ``"The Endurain team"``.

    Returns:
        A partial HTML string that closes all tags opened by
        :func:`html_header`.
    """
    return f"""
        </div>

        <div style="text-align: center; font-size: 12px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p>Best regards,<br>{sign_off}</p>
            <p>Visit Endurain at: <a style="color: {link_color};" href="{frontend_host}">{frontend_host}</a> -
                Source code at: <a style="color: {link_color};"
                    href="https://github.com/endurain-project/endurain">GitHub</a></p>
        </div>
    </div>
</body>

</html>"""
