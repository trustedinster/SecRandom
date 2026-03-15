from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SettingsPageRegistration:
    route_name: str
    interface_attr: str
    item_attr: str
    page_method: str
    is_pivot: bool
    icon_name: str
    language_module: str
    sidebar_setting_key: str
    title_key: str = "title"
    url_alias: str | None = None


SETTINGS_PAGE_REGISTRY: tuple[SettingsPageRegistration, ...] = (
    SettingsPageRegistration(
        route_name="settings_basic",
        interface_attr="basicSettingsInterface",
        item_attr="basic_settings_item",
        page_method="basic_settings_page",
        is_pivot=False,
        icon_name="ic_fluent_wrench_settings_20_filled",
        language_module="basic_settings",
        sidebar_setting_key="base_settings",
        url_alias="basic",
    ),
    SettingsPageRegistration(
        route_name="settings_list",
        interface_attr="listManagementInterface",
        item_attr="list_management_item",
        page_method="list_management_page",
        is_pivot=True,
        icon_name="ic_fluent_list_20_filled",
        language_module="list_management",
        sidebar_setting_key="name_management",
        url_alias="list",
    ),
    SettingsPageRegistration(
        route_name="settings_extraction",
        interface_attr="extractionSettingsInterface",
        item_attr="extraction_settings_item",
        page_method="extraction_settings_page",
        is_pivot=True,
        icon_name="ic_fluent_archive_20_filled",
        language_module="extraction_settings",
        sidebar_setting_key="draw_settings",
        url_alias="extraction",
    ),
    SettingsPageRegistration(
        route_name="settings_floating",
        interface_attr="floatingWindowManagementInterface",
        item_attr="floating_window_management_item",
        page_method="floating_window_management_page",
        is_pivot=True,
        icon_name="ic_fluent_window_apps_20_filled",
        language_module="floating_window_management",
        sidebar_setting_key="floating_window_management",
        url_alias="floating",
    ),
    SettingsPageRegistration(
        route_name="settings_notification",
        interface_attr="notificationSettingsInterface",
        item_attr="notification_settings_item",
        page_method="notification_settings_page",
        is_pivot=True,
        icon_name="ic_fluent_comment_note_20_filled",
        language_module="notification_settings",
        sidebar_setting_key="notification_service",
        url_alias="notification",
    ),
    SettingsPageRegistration(
        route_name="settings_safety",
        interface_attr="safetySettingsInterface",
        item_attr="safety_settings_item",
        page_method="safety_settings_page",
        is_pivot=True,
        icon_name="ic_fluent_shield_20_filled",
        language_module="safety_settings",
        sidebar_setting_key="security_settings",
        url_alias="safety",
    ),
    SettingsPageRegistration(
        route_name="settings_linkage",
        interface_attr="courseSettingsInterface",
        item_attr="course_settings_item",
        page_method="linkage_settings_page",
        is_pivot=False,
        icon_name="ic_fluent_calendar_ltr_20_filled",
        language_module="linkage_settings",
        sidebar_setting_key="linkage_settings",
    ),
    SettingsPageRegistration(
        route_name="settings_voice",
        interface_attr="voiceSettingsInterface",
        item_attr="voice_settings_item",
        page_method="voice_settings_page",
        is_pivot=True,
        icon_name="ic_fluent_person_voice_20_filled",
        language_module="voice_settings",
        sidebar_setting_key="voice_settings",
        url_alias="voice",
    ),
    SettingsPageRegistration(
        route_name="settings_theme",
        interface_attr="themeManagementInterface",
        item_attr="theme_management_item",
        page_method="theme_management_page",
        is_pivot=False,
        icon_name="ic_fluent_paint_brush_20_filled",
        language_module="theme_management",
        sidebar_setting_key="theme_management",
    ),
    SettingsPageRegistration(
        route_name="settings_history",
        interface_attr="historyInterface",
        item_attr="history_item",
        page_method="history_page",
        is_pivot=True,
        icon_name="ic_fluent_history_20_filled",
        language_module="history",
        sidebar_setting_key="settings_history",
        url_alias="history",
    ),
    SettingsPageRegistration(
        route_name="settings_more",
        interface_attr="moreSettingsInterface",
        item_attr="more_settings_item",
        page_method="more_settings_page",
        is_pivot=True,
        icon_name="ic_fluent_more_horizontal_20_filled",
        language_module="more_settings",
        sidebar_setting_key="more_settings",
        url_alias="more",
    ),
    SettingsPageRegistration(
        route_name="settings_update",
        interface_attr="updateInterface",
        item_attr="update_item",
        page_method="update_page",
        is_pivot=False,
        icon_name="ic_fluent_arrow_sync_20_filled",
        language_module="update",
        sidebar_setting_key="updateInterface",
        url_alias="update",
    ),
    SettingsPageRegistration(
        route_name="settings_about",
        interface_attr="aboutInterface",
        item_attr="about_item",
        page_method="about_page",
        is_pivot=False,
        icon_name="ic_fluent_info_20_filled",
        language_module="about",
        sidebar_setting_key="aboutInterface",
        url_alias="about",
    ),
)


MAIN_PAGE_ALIAS_MAP: dict[str, str] = {
    "roll": "roll_call_page",
    "lottery": "lottery_page",
    "history": "history_page",
}


SETTINGS_PAGE_BY_ROUTE: dict[str, SettingsPageRegistration] = {
    page.route_name: page for page in SETTINGS_PAGE_REGISTRY
}
SETTINGS_PAGE_BY_INTERFACE: dict[str, SettingsPageRegistration] = {
    page.interface_attr: page for page in SETTINGS_PAGE_REGISTRY
}
SETTINGS_PAGE_BY_ALIAS: dict[str, SettingsPageRegistration] = {
    page.url_alias: page for page in SETTINGS_PAGE_REGISTRY if page.url_alias
}


def iter_settings_pages() -> tuple[SettingsPageRegistration, ...]:
    return SETTINGS_PAGE_REGISTRY


def iter_navigable_settings_pages() -> tuple[SettingsPageRegistration, ...]:
    return SETTINGS_PAGE_REGISTRY


def iter_settings_page_container_names() -> tuple[str, ...]:
    return tuple(page.interface_attr for page in SETTINGS_PAGE_REGISTRY)


def get_settings_page_by_route(route_name: str) -> SettingsPageRegistration | None:
    return SETTINGS_PAGE_BY_ROUTE.get(route_name)


def get_settings_page_by_interface(
    interface_attr: str,
) -> SettingsPageRegistration | None:
    return SETTINGS_PAGE_BY_INTERFACE.get(interface_attr)


def get_settings_page_by_alias(alias: str) -> SettingsPageRegistration | None:
    return SETTINGS_PAGE_BY_ALIAS.get(alias)


def resolve_main_page_alias(alias: str) -> str | None:
    return MAIN_PAGE_ALIAS_MAP.get(alias)
