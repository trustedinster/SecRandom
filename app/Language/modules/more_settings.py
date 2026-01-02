# 更多设置语言配置
more_settings = {
    "ZH_CN": {
        "title": {"name": "更多设置", "description": "更多功能设置"},
    },
    "EN_US": {"title": {"name": "More settings", "description": "More settings"}},
}

settings = {
    "ZH_CN": {
        "title": {"name": "设置", "description": "设置窗口"},
    },
    "EN_US": {"title": {"name": "Settings", "description": "Settings window"}},
}

# 时间设置语言配置
time_settings = {
    "ZH_CN": {
        "title": {"name": "时间设置", "description": "设置课间禁用和课程表导入"},
        "class_break_settings": {
            "name": "课间禁用设置",
            "description": "设置课间禁用功能",
        },
        "cses_import_settings": {
            "name": "CSES课程表导入",
            "description": "从CSES格式文件导入课程表",
        },
        "class_break_function": {
            "name": "课间禁用功能",
            "description": "开启后，在下课时间段内抽取需要安全验证",
        },
        "cses_import": {
            "name": "课程表导入",
            "description": "从CSES格式文件导入上课时间段，用于课间禁用功能",
        },
        "verification_function": {
            "name": "验证流程功能",
            "description": "启用后，在非上课时段触发时将弹出安全验证；若关闭则直接禁用控件",
        },
        "class_island_source_function": {
            "name": "ClassIsland数据源",
            "description": "启用后，使用ClassIsland软件提供的课程表信息判断课间时间",
        },
        "import_from_file": {"name": "从文件导入"},
        "importing": {"name": "导入中..."},
        "view_current_config": {"name": "查看当前配置"},
        "no_schedule_imported": {"name": "未导入课程表"},
        "schedule_imported": {"name": "已导入 {} 个上课时间段"},
        "copy_to_clipboard": {"name": "复制到剪贴板"},
        "save_as_file": {"name": "保存为文件"},
        "copy_success": {"name": "复制成功"},
        "template_copied": {"name": "模板已复制到剪贴板"},
        "save_success": {"name": "保存成功"},
        "template_saved": {"name": "模板已保存到: {}"},
        "import_success": {"name": "成功导入课程表: {}"},
        "import_failed": {"name": "导入失败: {}"},
        "import_error": {"name": "导入过程中发生错误: {}"},
        "template_title": {"name": "CSES课程表模板"},
        "select_cses_file": {"name": "选择CSES课程表文件"},
        "yaml_files": {"name": "YAML文件 (*.yaml *.yml)"},
        "all_files": {"name": "所有文件 (*.*)"},
        "save_template": {"name": "保存CSES模板"},
        "cses_template": {"name": "cses_template.yaml"},
        "save_failed": {"name": "保存失败: {}"},
        "copy_failed": {"name": "复制失败: {}"},
        "cses_file_format_error": {"name": "CSES文件格式错误或文件无法读取"},
        "cses_content_format_error": {"name": "CSES内容格式错误"},
        "no_valid_time_periods": {"name": "未能从课程表中提取有效的时间段信息"},
        "save_settings_failed": {"name": "保存设置失败"},
        "no_cses_folder": {"name": "未找到CSES文件夹"},
        "no_schedule_file": {"name": "未导入课程表文件"},
        "unknown": {"name": "未知"},
        "unknown_course": {"name": "未知课程"},
        "parse_failed": {"name": "解析失败"},
        "load_config_failed": {"name": "加载配置失败: {}"},
        "table_headers": {"name": ["星期", "课程名称", "开始时间", "结束时间", "老师"]},
        "day_map": {
            "1": "周一",
            "2": "周二",
            "3": "周三",
            "4": "周四",
            "5": "周五",
            "6": "周六",
            "7": "周日",
        },
    },
    "EN_US": {
        "title": {"name": "时间设置", "description": "设置课间禁用和课程表导入"},
        "class_break_settings": {
            "name": "课间禁用设置",
            "description": "设置课间禁用功能",
        },
        "cses_import_settings": {
            "name": "CSES Schedule Importation",
            "description": "Import schedule from CSES file",
        },
        "class_break_function": {
            "name": "Disable draw during class break",
            "description": "Draw during class breaks need security authorization when enabled",
        },
        "cses_import": {
            "name": "Schedule import",
            "description": "Import class timetable from CSES file for auto-disable during class breaks",
        },
        "import_from_file": {"name": "Import from file"},
        "importing": {"name": "导入中..."},
        "view_template": {"name": "View template"},
        "no_schedule_imported": {"name": "Haven't imported schedule yet"},
        "copy_to_clipboard": {"name": "复制到剪贴板"},
        "save_as_file": {"name": "保存为文件"},
        "close": {"name": "Disabled"},
        "copy_success": {"name": "复制成功"},
        "template_copied": {"name": "Template has been copied to clipboard"},
        "save_success": {"name": "Item successfully saved"},
        "template_saved": {"name": "Template have been saved to: {}"},
        "import_error": {"name": "Error {} occurred when importing"},
        "template_title": {"name": "CSES schedule template"},
        "select_cses_file": {"name": "选择CSES课程表文件"},
        "yaml_files": {"name": "YAML文件 (*.yaml *.yml)"},
        "all_files": {"name": "所有文件 (*.*)"},
        "save_template": {"name": "保存CSES模板"},
        "cses_template": {"name": "cses_template.yaml"},
        "verification_function": {
            "name": "验证流程功能",
            "description": "启用后，在非上课时段触发时将弹出安全验证；若关闭则直接禁用控件",
        },
        "class_island_source_function": {
            "name": "ClassIsland data source",
            "description": "When enabled, use ClassIsland software's schedule information to determine class break times",
        },
        "view_current_config": {"name": "查看当前配置"},
        "schedule_imported": {"name": "已导入 {} 个上课时间段"},
        "import_success": {"name": "成功导入课程表: {}"},
        "import_failed": {"name": "导入失败: {}"},
        "save_failed": {"name": "保存失败: {}"},
        "copy_failed": {"name": "复制失败: {}"},
        "cses_file_format_error": {"name": "CSES文件格式错误或文件无法读取"},
        "cses_content_format_error": {"name": "CSES内容格式错误"},
        "no_valid_time_periods": {"name": "未能从课程表中提取有效的时间段信息"},
        "save_settings_failed": {"name": "保存设置失败"},
        "no_cses_folder": {"name": "未找到CSES文件夹"},
        "no_schedule_file": {"name": "未导入课程表文件"},
        "unknown": {"name": "未知"},
        "unknown_course": {"name": "未知课程"},
        "parse_failed": {"name": "解析失败"},
        "load_config_failed": {"name": "加载配置失败: {}"},
        "table_headers": {
            "name": {
                "0": "星期",
                "1": "课程名称",
                "2": "开始时间",
                "3": "结束时间",
                "4": "老师",
            }
        },
        "day_map": {
            "1": "周一",
            "2": "周二",
            "3": "周三",
            "4": "周四",
            "5": "周五",
            "6": "周六",
            "7": "周日",
        },
    },
}

# 快捷键设置
shortcut_settings = {
    "ZH_CN": {
        "title": {"name": "快捷键设置", "description": "设置快捷键功能"},
        "function": {"name": "功能"},
        "shortcut": {"name": "快捷键"},
        "press_shortcut": {"name": "点击此处设置快捷键"},
        "enable_shortcut": {
            "name": "启用快捷键",
            "description": "启用后可使用快捷键快速操作",
            "switchbutton_name": {"enable": "启用", "disable": "禁用"},
        },
        "open_roll_call_page": {"name": "打开点名页面"},
        "use_quick_draw": {"name": "使用闪抽"},
        "open_lottery_page": {"name": "打开抽奖页面"},
        "increase_roll_call_count": {"name": "增加点名人数"},
        "decrease_roll_call_count": {"name": "减少点名人数"},
        "increase_lottery_count": {"name": "增加抽奖人数"},
        "decrease_lottery_count": {"name": "减少抽奖人数"},
        "start_roll_call": {"name": "开始点名"},
        "start_lottery": {"name": "开始抽奖"},
    },
    "EN_US": {
        "title": {"name": "Shortcut settings", "description": "Shortcut settings"},
        "function": {"name": "Function"},
        "shortcut": {"name": "Shortcut"},
        "press_shortcut": {"name": "Click here to set shortcut"},
        "enable_shortcut": {
            "name": "Enable shortcut",
            "description": "Enable shortcuts for quick operations",
            "switchbutton_name": {"enable": "Enable", "disable": "Disable"},
        },
        "open_roll_call_page": {"name": "Open roll call page"},
        "use_quick_draw": {"name": "Use quick draw"},
        "open_lottery_page": {"name": "Open lottery page"},
        "increase_roll_call_count": {"name": "Increase roll call count"},
        "decrease_roll_call_count": {"name": "Decrease roll call count"},
        "increase_lottery_count": {"name": "Increase lottery count"},
        "decrease_lottery_count": {"name": "Decrease lottery count"},
        "start_roll_call": {"name": "Start roll call"},
        "start_lottery": {"name": "Start lottery"},
    },
}

# 关于语言配置
about = {
    "ZH_CN": {
        "title": {"name": "关于", "description": "软件关于页面信息"},
        "github": {"name": "Github", "description": "访问项目代码仓库"},
        "bilibili": {
            "name": "Bilibili",
            "description": "访问黎泽懿_Aionflux的Bilibili账号",
        },
        "contributor": {
            "name": "贡献人员",
            "description": "点击查看详细贡献者信息",
            "contributor_role_1": "设计、创意、策划\n维护、文档、测试",
            "contributor_role_2": "维护",
            "contributor_role_3": "响应式前端页面\n设计及维护、文档",
            "contributor_role_4": "创意、文档",
            "contributor_role_5": "创意、维护",
            "contributor_role_6": "应用测试、文档、安装包制作",
            "contributor_role_7": "响应式前端页面\n设计及维护、文档",
        },
        "donation": {"name": "捐赠支持", "description": "支持项目发展，感谢您的捐赠"},
        "website": {"name": "SecRandom 官网", "description": "访问SecRandom软件官网"},
        "copyright": {"name": "版权", "description": "SecRandom遵循GPL-3.0协议"},
        "version": {"name": "版本", "description": "显示当前软件版本号"},
    },
    "EN_US": {
        "title": {"name": "About", "description": "APP about page"},
        "github": {"name": "GitHub", "description": "Visit project repository"},
        "bilibili": {
            "name": "Bilibili",
            "description": "Visit 黎泽懿_Aionflux's Bilibili account",
        },
        "contributor": {
            "name": "Contributors",
            "description": "Click to show full contributor information",
            "contributor_role_1": "Design & Creativity & Test &\nMaintenance & Documentation",
            "contributor_role_2": "Maintenance",
            "contributor_role_3": "Responsive frontend page Design and Maintenance & Documentation",
            "contributor_role_4": "Creativity & Documentation",
            "contributor_role_5": "Creativity & Maintenance",
            "contributor_role_6": "Test & Documentation & Install Package Making",
            "contributor_role_7": "Responsive frontend page Design and Maintenance & Documentation",
        },
        "donation": {"name": "Donate", "description": "Buy me a coffee"},
        "check_update": {
            "name": "Check for updates",
            "description": "Check for updates",
        },
        "website": {
            "name": "SecRandom Website",
            "description": "Visit SecRandom's official website",
        },
        "channel": {
            "name": "Update channel",
            "description": "Select SecRandom software update channel",
            "combo_items": {"0": "Official version", "1": "Beta version"},
        },
        "copyright": {"name": "Copyright", "description": "SecRandom follows GPL-3.0"},
        "version": {"name": "Version", "description": "Show current version"},
    },
}

# 翻译文件信息
translate_JSON_file = {
    "ZH_CN": {
        "name": "简体中文",
        "translated_personnel": "lzy98276",
    },
    "EN_US": {
        "name": "English",
        "translated_personnel": "",
    },
}
