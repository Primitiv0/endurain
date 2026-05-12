"""Email message builders for password reset notifications."""

import html
from urllib.parse import quote as url_quote

import core.apprise as core_apprise
import core.email_templates as core_email_templates
import core.i18n as core_i18n


def get_password_reset_email(
    user_name: str,
    reset_link: str,
    email_service: core_apprise.AppriseService,
    locale: str | None = None,
) -> tuple[str, str, str]:
    """
    Build a localized password reset email.

    Args:
        user_name: The recipient's display name.
        reset_link: The URL for resetting the password.
        email_service: AppriseService for footer metadata.
        locale: Preferred locale code for the recipient.
            Falls back to ``"us"`` if unsupported or None.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(user_name)
    lang = core_i18n.html_lang(locale)

    def tr(key: str, **kwargs: str) -> str:
        return core_i18n.t(key, locale, **kwargs)

    subject = tr("password_reset.subject")
    heading = tr("password_reset.heading")
    greeting = tr("password_reset.greeting", name=safe_name)
    intro = tr("password_reset.intro")
    cta = tr("password_reset.cta")
    security_label = tr("password_reset.security_label")
    security_notice = tr("password_reset.security_notice")
    ignore = tr("password_reset.ignore")
    copy_link = tr("common.copy_link")
    best_regards = tr("common.best_regards")
    team = tr("common.team")
    visit = tr("common.visit")
    source_code = tr("common.source_code")

    frontend_host = html.escape(email_service.frontend_host)
    safe_reset_link = url_quote(reset_link, safe=":/?=&%#@")
    color = core_email_templates.LINK_COLOR_PRIMARY

    html_content = (
        core_email_templates.html_header(
            html.escape(subject), html.escape(heading), lang
        )
        + f"""
            <p>{greeting}</p>
            <p>{intro}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a
                    href="{safe_reset_link}"
                    style="background-color: {color}; color: white;
                    padding: 12px 30px; text-decoration: none;
                    border-radius: 5px; display: inline-block;
                    font-weight: bold;"
                >{cta}</a>
            </div>
            <div
                style="background-color: #fff3cd;
                border: 1px solid #ffeaa7; color: #856404;
                padding: 15px; border-radius: 5px; margin: 20px 0;"
            >
                <strong>{security_label}</strong> {security_notice}
            </div>
            <p>{ignore}</p>
            <p>{copy_link}</p>
            <p style="word-break: break-all; color: {color};">"""
        + f"""{safe_reset_link}</p>"""
        + core_email_templates.html_footer(
            frontend_host=frontend_host,
            link_color=color,
            best_regards=best_regards,
            sign_off=team,
            visit_label=visit,
            source_code_label=source_code,
        )
    )

    text_content = (
        f"{tr('password_reset.greeting', name=user_name)}\n\n"
        f"{intro}\n"
        f"{reset_link}\n\n"
        f"{security_notice}\n\n"
        f"{ignore}\n\n"
        f"{best_regards}\n"
        f"{team}"
    )

    return subject, html_content, text_content

