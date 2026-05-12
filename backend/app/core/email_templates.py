"""Shared HTML email template helpers for all Endurain email builders."""

# Bootstrap-derived brand colours used across email templates.
LINK_COLOR_PRIMARY = "#0d6efd"  # blue  – password reset
LINK_COLOR_SUCCESS = "#198754"  # green – sign-up flows

_LOGO_URL = (
    "https://codeberg.org/endurain-project/endurain/raw/branch/master/"
    "frontend/app/public/logo/logo.png"
)


def html_header(title: str, heading: str, lang: str = "en") -> str:
    """
    Return the opening HTML block shared by all Endurain emails.

    Includes the doctype, ``<head>``, ``<body>`` wrapper, branded logo
    header with ``heading``, and the opening tag of the content
    ``<div>`` that callers must fill and then close with
    :func:`html_footer`.

    Args:
        title: Value placed in ``<title>`` (typically the email
            subject).
        heading: Text rendered inside the ``<h3>`` below the logo.
        lang: BCP 47 language tag for the ``<html lang>`` attribute.
            Defaults to ``"en"``.

    Returns:
        A partial HTML string ending with an open ``<div
        style="margin-bottom: 30px;">``.
    """
    return f"""\
<!DOCTYPE html>
<html lang="{lang}">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>

<body
    style="font-family: Arial, sans-serif; line-height: 1.6;
    color: #333; max-width: 600px; margin: 0 auto; padding: 20px;
    background-color: #f4f4f4;"
>
    <div
        style="background-color: #ffffff; padding: 30px;
        border-radius: 10px; box-shadow: 0 2px 10px
        rgba(0, 0, 0, 0.1);"
    >
        <div style="text-align: center; margin-bottom: 30px;">
            <div
                style="font-size: 34px; font-weight: bold;
                margin-bottom: 10px; display: flex; align-items: center;
                justify-content: center; gap: 10px;"
            >
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
    best_regards: str = "Best regards,",
    sign_off: str = "The Endurain team",
    visit_label: str = "Visit Endurain at:",
    source_code_label: str = "Source code at:",
) -> str:
    """
    Return the closing HTML block shared by all Endurain emails.

    Closes the content ``<div>`` opened by :func:`html_header`,
    renders the footer with a sign-off greeting and links to the
    frontend host and the Codeberg repository, then closes the outer
    wrapper, ``<body>``, and ``<html>``.

    Args:
        frontend_host: Base URL of the Endurain frontend, shown in
            the footer link.
        link_color: CSS colour string applied to all footer anchor
            tags. Use module-level constants
            :data:`LINK_COLOR_PRIMARY` or
            :data:`LINK_COLOR_SUCCESS` for consistency.
        best_regards: Localized salutation line.
            Defaults to ``"Best regards,"``.
        sign_off: Localized team or system name for the sign-off.
            Defaults to ``"The Endurain team"``.
        visit_label: Localized label before the frontend URL.
            Defaults to ``"Visit Endurain at:"``.
        source_code_label: Localized label before the repo link.
            Defaults to ``"Source code at:"``.

    Returns:
        A partial HTML string that closes all tags opened by
        :func:`html_header`.
    """
    return f"""
        </div>

        <div
            style="text-align: center; font-size: 12px; color: #666;
            margin-top: 30px; padding-top: 20px;
            border-top: 1px solid #eee;"
        >
            <p>{best_regards}<br>{sign_off}</p>
            <p>
                {visit_label}
                <a style="color: {link_color};" href="{frontend_host}">
                    {frontend_host}
                </a> - {source_code_label}
                <a
                    style="color: {link_color};"
                    href="https://codeberg.org/endurain-project/endurain"
                >
                    Codeberg
                </a>
            </p>
        </div>
    </div>
</body>

</html>"""
