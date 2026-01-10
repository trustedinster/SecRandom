# 浮窗管理语言配置
floating_window_management = {
    "ZH_CN": {
        "title": {"name": "浮窗管理", "description": "配置浮窗相关设置"},
        "basic_settings": {"name": "基本设置", "description": "配置浮窗基本设置"},
        "appearance_settings": {
            "name": "外观设置",
            "description": "配置浮窗外观设置",
        },
        "edge_settings": {"name": "贴边设置", "description": "配置浮窗贴边设置"},
        "startup_display_floating_window": {
            "name": "启动时显示浮窗",
            "description": "控制软件启动时是否自动显示浮窗",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "floating_window_opacity": {
            "name": "浮窗透明度",
            "description": "调整浮窗透明度",
        },
        "reset_floating_window_position_button": {
            "name": "重置浮窗位置",
            "description": "将浮窗位置重置为默认位置",
            "pushbutton_name": "重置位置",
        },
        "floating_window_button_control": {
            "name": "浮窗控件配置",
            "description": "选择在浮窗中显示的功能按钮",
            "combo_items": [
                "点名",
                "闪抽",
                "抽奖",
                "点名+闪抽",
                "点名+抽奖",
                "闪抽+抽奖",
                "点名+闪抽+抽奖",
            ],
        },
        "floating_window_placement": {
            "name": "浮窗排列方式",
            "description": "设置浮窗中控件排列方式",
            "combo_items": ["矩形排列", "竖向排列", "横向排列"],
        },
        "floating_window_display_style": {
            "name": "浮窗显示样式",
            "description": "设置浮窗中控件显示样式",
            "combo_items": ["图标+文字", "图标", "文字"],
        },
        "floating_window_stick_to_edge": {
            "name": "贴边功能",
            "description": "控制浮窗是否自动贴边",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "floating_window_stick_to_edge_recover_seconds": {
            "name": "贴边收纳时间",
            "description": "设置浮窗贴边后自动收纳时间（秒）",
        },
        "floating_window_draggable": {
            "name": "浮窗可拖动",
            "description": "控制浮窗是否可被拖动",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "floating_window_long_press_duration": {
            "name": "长按时间",
            "description": "设置浮窗长按时间（毫秒）",
        },
        "floating_window_stick_to_edge_display_style": {
            "name": "贴边显示样式",
            "description": "设置浮窗贴边时显示样式",
            "combo_items": ["图标", "文字", "箭头"],
        },
        "floating_window_stick_to_edge_arrow_text": {
            "name": "抽",
            "description": "设置浮窗贴边时箭头按钮显示的文字",
        },
        "floating_window_size": {
            "name": "浮窗大小",
            "description": "设置浮窗按钮和图标的大小",
            "combo_items": ["超级小", "超小", "小", "中", "大", "超大", "超级大"],
        },
        "do_not_steal_focus": {
            "name": "无焦点模式",
            "description": "通知窗口显示时不抢占焦点，保持原有顶层软件焦点",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
    },
    "EN_US": {
        "title": {
            "name": "Floating window management",
            "description": "Configure floating window related settings",
        },
        "basic_settings": {
            "name": "Basic settings",
            "description": "Configure floating window basic settings",
        },
        "appearance_settings": {
            "name": "Appearance settings",
            "description": "Configure floating window appearance settings",
        },
        "edge_settings": {
            "name": "Edge settings",
            "description": "Configure floating window edge settings",
        },
        "startup_display_floating_window": {
            "name": "Show popup on startup",
            "description": "Set whether to show the floating window after boot",
        },
        "floating_window_opacity": {
            "name": "Floating window transparency",
            "description": "Adjust floating window transparency",
        },
        "reset_floating_window_position_button": {
            "name": "Reset floating window position",
            "description": "Reset floating window to default position",
            "pushbutton_name": "Reset position",
        },
        "floating_window_button_control": {
            "name": "Floating window controls config",
            "description": "Select the button to show in floating window",
            "combo_items": {
                "0": "Pick",
                "1": "Quick Pick",
                "2": "Instant Pick",
                "3": "Lottery",
                "4": "Pick + Quick Pick",
                "5": "Pick + Lottery",
                "6": "Quick Pick + Lottery",
                "7": "Pick + Quick Pick + Lottery",
            },
        },
        "floating_window_placement": {
            "name": "Floating window layout",
            "description": "Configure layout of buttons in floating window",
            "combo_items": {"0": "Rectangle", "1": "Portrait", "2": "Landscape"},
        },
        "floating_window_display_style": {
            "name": "Floating window style",
            "description": "Configure style of buttons in floating window",
            "combo_items": {"0": "Icon + Text", "1": "Icon only", "2": "Text only"},
        },
        "floating_window_stick_to_edge": {
            "name": "Edge function",
            "description": "Whether to dock floating window automatically",
        },
        "floating_window_stick_to_edge_recover_seconds": {
            "name": "Edge receipt time",
            "description": "Set the automatic reception time after the floating window near side (seconds)",
        },
        "floating_window_stick_to_edge_display_style": {
            "name": "Edge style",
            "description": "Configure docked floating window style",
            "combo_items": {"0": "Icon", "1": "Text", "2": "Arrow"},
        },
        "floating_window_long_press_duration": {
            "name": "Long press time",
            "description": "Set floating window long by time (milliseconds)",
        },
        "floating_window_draggable": {
            "name": "Floating window draggable",
            "description": "Set if floating window is draggable",
        },
        "floating_window_stick_to_edge_arrow_text": {
            "name": "Pick",
            "description": "Set the text to show on arrow button when the floating window is docked",
        },
        "floating_window_size": {
            "name": "Floating window size",
            "description": "Set the size of buttons and icons in floating window",
            "combo_items": {
                "0": "Extra Small",
                "1": "Very Small",
                "2": "Small",
                "3": "Medium",
                "4": "Large",
                "5": "Extra Large",
                "6": "Extra Extra Large",
            },
        },
        "do_not_steal_focus": {
            "name": "Focusless mode",
            "description": "Do not steal focus when notification window appears, keep focus on original top-level software",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
    },
}

# 侧边栏/托盘管理语言配置
sidebar_tray_management = {
    "ZH_CN": {
        "title": {
            "name": "侧边栏/托盘管理",
            "description": "配置侧边栏和系统托盘相关设置",
        }
    },
    "EN_US": {
        "title": {
            "name": "Sidebar/Tray management",
            "description": "Configure sidebar and system tray related settings",
        }
    },
}

# 主界面侧边栏语言配置
sidebar_management_window = {
    "ZH_CN": {
        "title": {
            "name": "主界面侧边栏",
            "description": "配置主界面侧边栏管理相关设置 (重启生效)",
        },
        "roll_call_sidebar_position": {
            "name": "点名侧边栏位置",
            "description": "配置点名功能在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "lottery_sidebar_position": {
            "name": "抽奖侧边栏位置",
            "description": "配置抽奖功能在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "main_window_history": {
            "name": "主窗口历史记录位置",
            "description": "配置历史记录功能在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "settings_icon": {
            "name": "设置图标位置",
            "description": "配置设置图标在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
    },
    "EN_US": {
        "title": {
            "name": "Home sidebar",
            "description": "Configure home sidebar related settings",
        },
        "roll_call_sidebar_position": {
            "name": "Position of Picking",
            "description": "Set the position of Pick in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
        "lottery_sidebar_position": {
            "name": "Position of Lottery",
            "description": "Set the position of Lottery in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
        "main_window_history": {
            "name": "Main window history position",
            "description": "Set history position in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
        "settings_icon": {
            "name": "Set icon position",
            "description": "Set the position of Settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
    },
}

# 设置窗口侧边栏语言配置
sidebar_management_settings = {
    "ZH_CN": {
        "title": {
            "name": "设置窗口侧边栏",
            "description": "配置设置窗口侧边栏 (重启生效)",
        },
        "base_settings": {
            "name": "基础设置位置",
            "description": "设置基础设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "name_management": {
            "name": "名单管理位置",
            "description": "设置名单管理项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "draw_settings": {
            "name": "抽取设置位置",
            "description": "设置抽取设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "floating_window_management": {
            "name": "浮窗管理位置",
            "description": "设置浮窗管理项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "notification_service": {
            "name": "通知服务位置",
            "description": "设置通知服务项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "security_settings": {
            "name": "安全设置位置",
            "description": "设置安全设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "personal_settings": {
            "name": "个性设置位置",
            "description": "设置个性设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部"],
        },
        "voice_settings": {
            "name": "语音设置位置",
            "description": "设置语音设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "settings_history": {
            "name": "设置历史记录位置",
            "description": "设置历史记录项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
        "more_settings": {
            "name": "更多设置位置",
            "description": "设置更多设置项在侧边栏位置 (重启生效)",
            "combo_items": ["顶部", "底部", "不显示"],
        },
    },
    "EN_US": {
        "title": {
            "name": "Set window sidebar",
            "description": "Configure set window sidebar",
        },
        "home": {
            "name": "Home position",
            "description": "Set the position of Home in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
        "base_settings": {
            "description": "Set the position of Basic settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Basic position settings",
        },
        "name_management": {
            "description": "Set the position of List management in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of List management",
        },
        "draw_settings": {
            "description": "Set the position of Picking settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of Pick settings",
        },
        "floating_window_management": {
            "name": "Floating window management position",
            "description": "Set the position of Floating window management in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
        },
        "notification_service": {
            "description": "Set the position of Notification settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of Notification settings",
        },
        "security_settings": {
            "description": "Set the position of Safety settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of Security settings",
        },
        "personal_settings": {
            "description": "Set the position of Custom settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom"},
            "name": "Position of Profile settings",
        },
        "voice_settings": {
            "description": "Set the position of Voice settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of Voice settings",
        },
        "settings_history": {
            "description": "Set history position in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Set history position",
        },
        "more_settings": {
            "description": "Set the position of More settings in sidebar (Restart to take effect)",
            "combo_items": {"0": "Top", "1": "Bottom", "2": "Hide"},
            "name": "Position of More settings",
        },
    },
}

# 托盘管理语言配置
tray_management = {
    "ZH_CN": {
        "title": {"name": "托盘管理", "description": "配置系统托盘相关设置"},
        "show_hide_main_window": {
            "name": "暂时显示/隐藏主界面",
            "description": "控制主界面显示和隐藏",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "open_settings": {
            "name": "打开设置窗口",
            "description": "控制是否在托盘菜单中显示设置窗口选项",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "show_hide_float_window": {
            "name": "暂时显示/隐藏浮窗",
            "description": "控制浮窗显示和隐藏",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "restart": {
            "name": "重启应用",
            "description": "控制是否在托盘菜单中显示重启选项",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
        "exit": {
            "name": "退出应用",
            "description": "控制是否在托盘菜单中显示退出选项",
            "switchbutton_name": {"enable": "", "disable": ""},
        },
    },
    "EN_US": {
        "title": {
            "name": "Tray management",
            "description": "Configure system tray related settings",
        },
        "show_hide_main_window": {
            "name": "Show/hide main window",
            "description": "Control whether main window to show or not",
        },
        "open_settings": {
            "name": "Open settings window",
            "description": "Control whether to show settings option in the tray menu",
        },
        "show_hide_float_window": {
            "name": "Show/hide float window",
            "description": "Control whether floating window to show or not",
        },
        "restart": {
            "name": "Restart app",
            "description": "Control whether to show restart option in the tray menu",
        },
        "exit": {
            "name": "Exit app",
            "description": "Control whether to show exit option in the tray menu",
        },
    },
}
