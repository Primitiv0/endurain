"""Email message builders for sign-up notifications."""

import html
from urllib.parse import quote as url_quote

import core.apprise as core_apprise
import core.email_templates as core_email_templates
import core.i18n as core_i18n


def get_signup_confirmation_email(
    user_name: str,
    signup_link: str,
    email_service: core_apprise.AppriseService,
    locale: str | None = None,
) -> tuple[str, str, str]:
    """Build a localized sign-up confirmation email.

    Args:
        user_name: The recipient's display name.
        signup_link: The URL to confirm the account.
        email_service: AppriseService for footer metadata.
        locale: Preferred locale code for the recipient.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(user_name)
    lang = core_i18n.html_lang(locale)

    def tr(key: str, **kwargs: str) -> str:
        return core_i18n.t(key, locale, **kwargs)

    subject = tr("signup_confirmation.subject")
    heading = tr("signup_confirmation.heading")
    greeting = tr("signup_confirmation.greeting", name=safe_name)
    intro = tr("signup_confirmation.intro")
    cta = tr("signup_confirmation.cta")
    security_label = tr("signup_confirmation.security_label")
    security_notice = tr("signup_confirmation.security_notice")
    ignore = tr("signup_confirmation.ignore")
    copy_link = tr("common.copy_link")
    best_regards = tr("common.best_regards")
    team = tr("common.team")
    visit = tr("common.visit")
    source_code = tr("common.source_code")

    frontend_host = html.escape(email_service.frontend_host)
    safe_signup_link = url_quote(signup_link, safe=":/?=&%#@")
    color = core_email_templates.LINK_COLOR_SUCCESS

    html_content = (
        core_email_templates.html_header(
            html.escape(subject), html.escape(heading), lang
        )
        + f"""
            <p>{greeting}</p>
            <p>{intro}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a
                    href="{safe_signup_link}"
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
        + f"""{safe_signup_link}</p>"""
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
        f"{tr('signup_confirmation.greeting', name=user_name)}\n\n"
        f"{intro}\n"
        f"{signup_link}\n\n"
        f"{security_notice}\n\n"
        f"{ignore}\n\n"
        f"{best_regards}\n"
        f"{team}"
    )

    return subject, html_content, text_content


def get_admin_signup_notification_email(
    user_name: str,
    sign_up_user_name: str,
    sign_up_user_username: str,
    email_service: core_apprise.AppriseService,
    locale: str | None = None,
) -> tuple[str, str, str]:
    """Build a localized admin notification email.

    Args:
        user_name: Display name of the admin recipient.
        sign_up_user_name: Display name of the signed-up user.
        sign_up_user_username: Username of the signed-up user.
        email_service: AppriseService for footer metadata.
        locale: Preferred locale code for the admin recipient.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(user_name)
    safe_sign_up_name = html.escape(sign_up_user_name)
    lang = core_i18n.html_lang(locale)

    def tr(key: str, **kwargs: str) -> str:
        return core_i18n.t(key, locale, **kwargs)

    subject = tr("admin_signup.subject")
    heading = tr("admin_signup.heading")
    greeting = tr("admin_signup.greeting", name=safe_name)
    intro = tr("admin_signup.intro")
    user_label = tr("admin_signup.user_label")
    review = tr("admin_signup.review")
    cta = tr("admin_signup.cta")
    copy_link = tr("common.copy_link")
    best_regards = tr("common.best_regards")
    system = tr("common.system")
    visit = tr("common.visit")
    source_code = tr("common.source_code")

    frontend_host = html.escape(email_service.frontend_host)
    color = core_email_templates.LINK_COLOR_SUCCESS

    # URL-encode username for query-string safety.
    encoded_username = url_quote(sign_up_user_username, safe="")
    admin_link = (
        f"{email_service.frontend_host}"
        f"/settings?tab=users&username={encoded_username}"
    )
    safe_admin_link = html.escape(admin_link)

    html_content = (
        core_email_templates.html_header(
            html.escape(subject), html.escape(heading), lang
        )
        + f"""
            <p>{greeting}</p>
            <p>{intro}</p>
            <div
                style="background-color: #e9ecef;
                border: 1px solid #ccc; padding: 15px;
                border-radius: 5px; margin: 20px 0;"
            >
                <strong>{user_label}</strong> {safe_sign_up_name}
            </div>
            <p>{review}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a
                    href="{safe_admin_link}"
                    style="background-color: {color}; color: white;
                    padding: 12px 30px; text-decoration: none;
                    border-radius: 5px; display: inline-block;
                    font-weight: bold;"
                >{cta}</a>
            </div>
            <p>{copy_link}</p>
            <p style="word-break: break-all; color: {color};">"""
        + f"""{safe_admin_link}</p>"""
        + core_email_templates.html_footer(
            frontend_host=frontend_host,
            link_color=color,
            best_regards=best_regards,
            sign_off=system,
            visit_label=visit,
            source_code_label=source_code,
        )
    )

    text_content = (
        f"{tr('admin_signup.greeting', name=user_name)}\n\n"
        f"{intro}\n"
        f"{user_label} {sign_up_user_name}\n\n"
        f"{review}\n"
        f"{admin_link}\n\n"
        f"{best_regards}\n"
        f"{system}"
    )

    return subject, html_content, text_content


def get_user_signup_approved_email(
    sign_up_user_name: str,
    sign_up_user_username: str,
    email_service: core_apprise.AppriseService,
    locale: str | None = None,
) -> tuple[str, str, str]:
    """Build a localized account-approved notification email.

    Args:
        sign_up_user_name: Display name of the approved user.
        sign_up_user_username: Username of the approved user.
        email_service: AppriseService for footer metadata.
        locale: Preferred locale code for the approved user.

    Returns:
        A 3-tuple of (subject, html_content, text_content).
    """
    safe_name = html.escape(sign_up_user_name)
    safe_username = html.escape(sign_up_user_username)
    lang = core_i18n.html_lang(locale)

    def tr(key: str, **kwargs: str) -> str:
        return core_i18n.t(key, locale, **kwargs)

    subject = tr("signup_approved.subject")
    heading = tr("signup_approved.heading")
    greeting = tr("signup_approved.greeting", name=safe_name)
    intro = tr("signup_approved.intro")
    username_label = tr("signup_approved.username_label")
    login_intro = tr("signup_approved.login_intro")
    cta = tr("signup_approved.cta")
    copy_link = tr("common.copy_link")
    best_regards = tr("common.best_regards")
    team = tr("common.team")
    visit = tr("common.visit")
    source_code = tr("common.source_code")

    frontend_host = html.escape(email_service.frontend_host)
    color = core_email_templates.LINK_COLOR_SUCCESS
    login_link = f"{email_service.frontend_host}/login"
    safe_login_link = html.escape(login_link)

    html_content = (
        core_email_templates.html_header(
            html.escape(subject), html.escape(heading), lang
        )
        + f"""
            <p>{greeting}</p>
            <p>{intro}</p>
            <div
                style="background-color: #e9ecef;
                border: 1px solid #ccc; padding: 15px;
                border-radius: 5px; margin: 20px 0;"
            >
                <strong>{username_label}</strong> {safe_username}
            </div>
            <p>{login_intro}</p>
            <div style="text-align: center; margin: 30px 0;">
                <a
                    href="{safe_login_link}"
                    style="background-color: {color}; color: white;
                    padding: 12px 30px; text-decoration: none;
                    border-radius: 5px; display: inline-block;
                    font-weight: bold;"
                >{cta}</a>
            </div>
            <p>{copy_link}</p>
            <p style="word-break: break-all; color: {color};">"""
        + f"""{safe_login_link}</p>"""
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
        f"{tr('signup_approved.greeting', name=sign_up_user_name)}\n\n"
        f"{intro}\n"
        f"{username_label} {sign_up_user_username}\n\n"
        f"{login_intro}\n"
        f"{login_link}\n\n"
        f"{best_regards}\n"
        f"{team}"
    )

    return subject, html_content, text_content
