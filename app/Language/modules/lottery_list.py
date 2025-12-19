# 奖池名称设置窗口
set_prize_name = {
    "ZH_CN": {
        "title": {"name": "奖池名称设置", "description": "设置奖池名称窗口标题"},
        "description": {
            "name": "在此窗口中，您可以设置奖池名称\n每行输入一个奖池名称，系统会将其存储到奖池名单文件中\n\n请每行只输入一个奖池名称，例如：\n奖池一\n奖池二\n奖池三",
            "description": "奖池名称设置窗口描述",
        },
        "input_title": {"name": "奖池名称列表", "description": "奖池名称输入区域标题"},
        "input_placeholder": {
            "name": "请输入奖池名称，每行一个奖池名称",
            "description": "奖池名称输入框占位符",
        },
        "save_button": {"name": "保存", "description": "保存按钮文本"},
        "cancel_button": {"name": "取消", "description": "取消按钮文本"},
        "error_title": {"name": "错误", "description": "错误消息标题"},
        "success_title": {"name": "成功", "description": "成功消息标题"},
        "info_title": {"name": "提示", "description": "信息消息标题"},
        "invalid_names_error": {
            "name": "以下奖池名称包含非法字符或为保留字: {names}",
            "description": "奖池名称验证失败时的错误提示",
        },
        "save_error": {
            "name": "保存奖池名称失败",
            "description": "保存奖池名称时的错误提示",
        },
        "success_message": {
            "name": "成功创建 {count} 个新奖池",
            "description": "成功创建奖池时的提示消息",
        },
        "no_new_prizes_message": {
            "name": "所有奖池名称均已存在，未创建新的奖池",
            "description": "没有创建新奖池时的提示消息",
        },
        "unsaved_changes_title": {
            "name": "未保存的更改",
            "description": "未保存更改对话框标题",
        },
        "unsaved_changes_message": {
            "name": "您有未保存的更改，确定要关闭窗口吗？",
            "description": "未保存更改对话框内容",
        },
        "discard_button": {"name": "放弃更改", "description": "放弃更改按钮文本"},
        "continue_editing_button": {
            "name": "继续编辑",
            "description": "继续编辑按钮文本",
        },
        "delete_prize_title": {"name": "删除奖池", "description": "删除奖池对话框标题"},
        "delete_prize_message": {
            "name": "确定要删除奖池 '{prize_name}' 吗？此操作将删除该奖池的所有数据，且不可恢复",
            "description": "删除奖池确认对话框内容",
        },
        "delete_prize_button": {"name": "删除奖池", "description": "删除奖池按钮文本"},
        "delete_multiple_prizes_title": {
            "name": "删除多个奖池",
            "description": "删除多个奖池对话框标题",
        },
        "delete_multiple_prizes_message": {
            "name": "确定要删除以下 {count} 个奖池吗？此操作将删除这些奖池的所有数据，且不可恢复\n\n{prize_names}",
            "description": "删除多个奖池确认对话框内容",
        },
        "delete_success_title": {"name": "删除成功", "description": "删除成功通知标题"},
        "delete_success_message": {
            "name": "成功删除 {count} 个奖池",
            "description": "删除成功通知内容",
        },
        "delete_cancel_button": {"name": "取消删除", "description": "取消删除按钮文本"},
        "no_deletable_prizes": {
            "name": "没有可删除的奖池",
            "description": "没有可删除奖池时的提示",
        },
        "select_prize_to_delete": {
            "name": "请选择要删除的奖池",
            "description": "选择删除奖池的提示",
        },
        "select_prize_dialog_title": {
            "name": "选择要删除的奖池",
            "description": "选择删除奖池对话框标题",
        },
        "select_prize_dialog_message": {
            "name": "请选择要删除的奖池：",
            "description": "选择删除奖池对话框内容",
        },
        "delete_selected_button": {
            "name": "删除选中",
            "description": "删除选中按钮文本",
        },
        "delete_prize_error": {
            "name": "删除奖池失败: {error}",
            "description": "删除奖池失败错误信息",
        },
        "prize_disappeared_title": {
            "name": "奖池消失提示",
            "description": "奖池消失提示标题",
        },
        "prize_disappeared_message": {
            "name": "检测到奖池 '{prize_name}' 已从输入框中移除，请保存更改以永久删除",
            "description": "单个奖池消失提示内容",
        },
        "multiple_prizes_disappeared_message": {
            "name": "检测到以下 {count} 个奖池已从输入框中移除，请保存更改以永久删除：\n{prize_names}",
            "description": "多个奖池消失提示内容",
        },
    },
}

# 导入奖池名称语言配置
import_prize_name = {
    "ZH_CN": {
        "title": {
            "name": "导入奖池名称",
            "description": "从Excel或CSV文件导入奖池名称",
        },
        "initial_subtitle": {
            "name": "正在导入到：",
            "description": "正在导入到奖池的提示",
        },
        "file_selection_title": {"name": "文件选择", "description": "文件选择区域标题"},
        "no_file_selected": {
            "name": "未选择文件",
            "description": "未选择文件时的提示文本",
        },
        "select_file": {"name": "选择文件", "description": "选择文件按钮文本"},
        "supported_formats": {
            "name": "支持的格式: Excel (.xlsx, .xls) 和 CSV (.csv)",
            "description": "支持的文件格式说明",
        },
        "file_filter": {
            "name": "Excel 文件 (*.xlsx *.xls);;CSV 文件 (*.csv)",
            "description": "文件选择对话框的文件过滤器",
        },
        "dialog_title": {"name": "选择文件", "description": "文件选择对话框标题"},
        "column_mapping_title": {"name": "列映射", "description": "列映射区域标题"},
        "column_mapping_description": {
            "name": "请选择包含奖池信息的列",
            "description": "列映射区域说明",
        },
        "column_mapping_id_column": {
            "name": "序号列 (必选):",
            "description": "序号列标签",
        },
        "column_mapping_name_column": {
            "name": "奖池名称列 (必选):",
            "description": "奖池名称列标签",
        },
        "column_mapping_weight_column": {
            "name": "权重列 (可选):",
            "description": "权重列标签",
        },
        "column_mapping_none": {"name": "无", "description": "无选项文本"},
        "data_preview_title": {"name": "数据预览", "description": "数据预览区域标题"},
        "prize_id": {"name": "序号", "description": "序号列标题"},
        "prize_name": {"name": "奖池名称", "description": "奖池名称列标题"},
        "weight": {"name": "权重", "description": "权重列标题"},
        "buttons_import": {"name": "导入", "description": "导入按钮文本"},
        "file_loaded_title": {
            "name": "文件已加载",
            "description": "文件加载成功对话框标题",
        },
        "file_loaded_content": {
            "name": "文件加载成功",
            "description": "文件加载成功对话框内容",
        },
        "file_loaded_notification_title": {
            "name": "文件加载成功",
            "description": "文件加载成功通知标题",
        },
        "file_loaded_notification_content": {
            "name": "文件已成功加载，请检查数据预览",
            "description": "文件加载成功通知内容",
        },
        "error_title": {"name": "错误", "description": "错误对话框标题"},
        "load_failed": {"name": "加载文件失败", "description": "加载文件失败错误信息"},
        "load_failed_notification_title": {
            "name": "加载文件失败",
            "description": "加载文件失败通知标题",
        },
        "load_failed_notification_content": {
            "name": "无法加载文件，请检查文件格式和内容",
            "description": "加载文件失败通知内容",
        },
        "import_failed": {
            "name": "导入数据失败",
            "description": "导入数据失败错误信息",
        },
        "import_failed_notification_title": {
            "name": "导入数据失败",
            "description": "导入数据失败通知标题",
        },
        "import_failed_notification_content": {
            "name": "导入数据时发生错误，请检查数据格式和内容",
            "description": "导入数据失败通知内容",
        },
        "unsupported_format": {
            "name": "不支持的文件格式",
            "description": "不支持的文件格式错误信息",
        },
        "no_name_column": {
            "name": "请选择奖池名称列",
            "description": "未选择奖池名称列错误信息",
        },
        "no_id_column": {"name": "请选择序号列", "description": "未选择序号列错误信息"},
        "import_success_title": {
            "name": "导入成功",
            "description": "导入成功对话框标题",
        },
        "import_success_content_template": {
            "name": "成功导入 {count} 个奖池信息到奖池 '{prize_name}'",
            "description": "导入成功对话框内容模板",
        },
        "import_success_notification_title": {
            "name": "导入成功",
            "description": "导入成功通知标题",
        },
        "import_success_notification_content_template": {
            "name": "成功导入 {count} 个奖池信息到奖池 '{prize_name}'",
            "description": "导入成功通知内容模板",
        },
        "existing_data_title": {
            "name": "奖池已有数据",
            "description": "奖池已有数据对话框标题",
        },
        "existing_data_prompt": {
            "name": "奖池 '{prize_name}' 已包含 {count} 个奖池信息，请选择处理方式:",
            "description": "奖池已有数据对话框提示文本",
        },
        "existing_data_option_overwrite": {
            "name": "覆盖现有数据",
            "description": "覆盖现有数据选项",
        },
        "existing_data_option_cancel": {
            "name": "取消导入",
            "description": "取消导入选项",
        },
    },
    "EN_US": {
        "title": {
            "name": "Import pool name",
            "description": "Import pool name from Excel or CSV file",
        },
        "initial_subtitle": {
            "name": "Importing to:",
            "description": "Importing to the prize pool tips",
        },
        "file_selection_title": {
            "name": "File select",
            "description": "File Selection Area Title",
        },
        "no_file_selected": {
            "name": "No file selected",
            "description": "Hint text when no file is selected",
        },
        "select_file": {
            "name": "File select",
            "description": "Select File Button Text",
        },
        "supported_formats": {
            "name": "Supported formats: Excel (.xlsx, .xls) and CSV (.csv)",
            "description": "Supported File Format Description",
        },
        "file_filter": {
            "name": "Excel files (*.xlsx *.xls);;CSV files (*.csv)",
            "description": "File selection dialog filters",
        },
        "dialog_title": {
            "name": "File select",
            "description": "File selection dialog title",
        },
        "column_mapping_title": {
            "name": "Column mapping",
            "description": "Column map area title",
        },
        "column_mapping_description": {
            "name": "Please select a column containing the bonus pool information",
            "description": "Column map area description",
        },
        "column_mapping_id_column": {
            "name": "Serial column (required):",
            "description": "Serial column label",
        },
        "column_mapping_name_column": {
            "name": "Pool Name Column (required):",
            "description": "Pool Name List Label",
        },
        "column_mapping_weight_column": {
            "name": "Weight column (optional):",
            "description": "Reorder Tags",
        },
        "column_mapping_none": {
            "name": "None",
            "description": "Text of None",
        },
        "data_preview_title": {
            "name": "Data preview",
            "description": "Preview Area Title",
        },
        "prize_id": {
            "name": "No.",
            "description": "Serial column title",
        },
        "prize_name": {
            "name": "Pool Name",
            "description": "Pool Name Column Title",
        },
        "weight": {
            "name": "Weight",
            "description": "Reorder Title",
        },
        "buttons_import": {
            "name": "Import",
            "description": "Button text of Import",
        },
        "file_loaded_title": {
            "name": "File loaded",
            "description": "File loaded successfully dialog title",
        },
        "file_loaded_content": {
            "name": "Files loaded successfully",
            "description": "File loaded successfully dialog content",
        },
        "file_loaded_notification_title": {
            "name": "Files loaded successfully",
            "description": "File loaded with successful notification header",
        },
        "file_loaded_notification_content": {
            "name": "File successfully loaded, please check data preview",
            "description": "File loaded with successful notifications",
        },
        "error_title": {
            "name": "Error",
            "description": "Dialog title of Error",
        },
        "load_failed": {
            "name": "Failed to load files",
            "description": "Failed to load file error",
        },
        "load_failed_notification_title": {
            "name": "Failed to load files",
            "description": "Failed to load file notification title",
        },
        "load_failed_notification_content": {
            "name": "Could not load file. Please check file format and content",
            "description": "Failed to load notification content",
        },
        "import_failed": {
            "name": "Failed to import data",
            "description": "Error importing data",
        },
        "import_failed_notification_title": {
            "name": "Failed to import data",
            "description": "Failed to import data notification title",
        },
        "import_failed_notification_content": {
            "name": "Error importing data. Please check data format and content",
            "description": "Failed to import data content",
        },
        "unsupported_format": {
            "name": "Unsupported File Format",
            "description": "Unsupported file format error",
        },
        "no_name_column": {
            "name": "Please select a pool name column",
            "description": "List of award names not selected",
        },
        "no_id_column": {
            "name": "Please select serial number column",
            "description": "No serial number error selected",
        },
        "import_success_title": {
            "name": "Import success",
            "description": "Import successful dialog title",
        },
        "import_success_content_template": {
            "name": "成功导入 {count} 个奖池信息到奖池 '{prize_name}'",
            "description": "Import successful dialog content template",
        },
        "import_success_notification_title": {
            "name": "Import success",
            "description": "Import successful notification title",
        },
        "import_success_notification_content_template": {
            "name": "成功导入 {count} 个奖池信息到奖池 '{prize_name}'",
            "description": "Import successful notification content template",
        },
        "existing_data_title": {
            "name": "Bonus already has data",
            "description": "Holds already have data dialog title",
        },
        "existing_data_prompt": {
            "name": "奖池 '{prize_name}' 已包含 {count} 个奖池信息，请选择处理方式:",
            "description": "Bonus already has data dialog tip text",
        },
        "existing_data_option_overwrite": {
            "name": "Overwrite existing data",
            "description": "Overwrite existing data options",
        },
        "existing_data_option_cancel": {
            "name": "Cancel import",
            "description": "Option of Cancel import",
        },
    },
}

# 名称设置窗口
lottery_name_setting = {
    "ZH_CN": {
        "title": {"name": "奖品名称设置", "description": "设置奖品名称窗口标题"},
        "description": {
            "name": "在此窗口中，您可以设置奖品名称\n每行输入一个奖品名称，系统会将其存储到奖品名单文件中\n\n请每行只输入一个奖品名称，例如：\n一等奖\n二等奖\n三等奖",
            "description": "奖品名称设置窗口描述",
        },
        "input_title": {"name": "奖品名称列表", "description": "奖品名称输入区域标题"},
        "input_placeholder": {
            "name": "请输入奖品名称，每行一个奖品名称",
            "description": "奖品名称输入框占位符",
        },
        "save_button": {"name": "保存", "description": "保存按钮文本"},
        "cancel_button": {"name": "取消", "description": "取消按钮文本"},
        "error_title": {"name": "错误", "description": "错误消息标题"},
        "success_title": {"name": "成功", "description": "成功消息标题"},
        "info_title": {"name": "提示", "description": "信息消息标题"},
        "no_names_error": {
            "name": "请至少输入一个奖品名称",
            "description": "未输入奖品名称时的错误提示",
        },
        "invalid_names_error": {
            "name": "以下奖品名称包含非法字符或为保留字: {names}",
            "description": "奖品名称验证失败时的错误提示",
        },
        "save_error": {
            "name": "保存奖品名称失败",
            "description": "保存奖品名称时的错误提示",
        },
        "success_message": {
            "name": "成功创建 {count} 个新奖品名称",
            "description": "成功创建奖品名称时的提示消息",
        },
        "no_new_names_message": {
            "name": "所有奖品名称均已存在，未创建新的奖品名称",
            "description": "没有创建新奖品名称时的提示消息",
        },
        "unsaved_changes_title": {
            "name": "未保存的更改",
            "description": "未保存更改对话框标题",
        },
        "unsaved_changes_message": {
            "name": "您有未保存的更改，确定要关闭窗口吗？",
            "description": "未保存更改对话框内容",
        },
        "discard_button": {"name": "放弃更改", "description": "放弃更改按钮文本"},
        "continue_editing_button": {
            "name": "继续编辑",
            "description": "继续编辑按钮文本",
        },
        "delete_button": {"name": "删除", "description": "删除按钮文本"},
        "delete_name_title": {
            "name": "删除奖品名称",
            "description": "删除奖品名称对话框标题",
        },
        "delete_name_message": {
            "name": "确定要删除名称 '{name}' 吗？此操作将删除该名称的所有信息，且不可恢复",
            "description": "删除奖品名称确认对话框内容",
        },
        "delete_multiple_names_title": {
            "name": "删除多个奖品名称",
            "description": "删除多个奖品名称对话框标题",
        },
        "delete_multiple_names_message": {
            "name": "确定要删除以下 {count} 个奖品名称吗？此操作将删除这些奖品名称的所有信息，且不可恢复\n\n{names}",
            "description": "删除多个名称确认对话框内容",
        },
        "delete_name_success_title": {
            "name": "删除成功",
            "description": "删除奖品名称成功通知标题",
        },
        "delete_name_success_message": {
            "name": "成功删除 {count} 个奖品名称",
            "description": "删除奖品名称成功通知内容",
        },
        "delete_name_cancel_button": {
            "name": "取消删除",
            "description": "取消删除奖品名称按钮文本",
        },
        "no_deletable_names": {
            "name": "没有可删除的奖品名称",
            "description": "没有可删除奖品名称时的提示",
        },
        "select_name_to_delete": {
            "name": "请选择要删除的奖品名称",
            "description": "选择删除奖品名称的提示",
        },
        "select_name_dialog_title": {
            "name": "选择要删除的奖品名称",
            "description": "选择删除奖品名称对话框标题",
        },
        "select_name_dialog_message": {
            "name": "请选择要删除的奖品名称：",
            "description": "选择删除奖品名称对话框内容",
        },
        "delete_selected_names_button": {
            "name": "删除选中",
            "description": "删除选中奖品名称按钮文本",
        },
        "delete_name_error": {
            "name": "删除奖品名称失败: {error}",
            "description": "删除奖品名称失败错误信息",
        },
        "name_deleted_title": {
            "name": "奖品名称已删除",
            "description": "删除奖品名称提示标题",
        },
        "name_deleted_message": {
            "name": "奖品名称 '{name}' 已从输入框中删除，请保存更改以永久删除",
            "description": "删除奖品名称提示内容",
        },
    },
}

# 权重设置窗口
weight_setting = {
    "ZH_CN": {
        "title": {"name": "权重设置", "description": "设置权重窗口标题"},
        "description": {
            "name": "在此窗口中，您可以设置奖品的权重\n每行输入一个权重值，系统会将其存储到奖品名单文件中\n\n请每行只输入一个权重值，例如：\n10\n20\n30",
            "description": "权重设置窗口描述",
        },
        "input_title": {"name": "权重列表", "description": "权重输入区域标题"},
        "input_placeholder": {
            "name": "请输入权重，每行一个权重",
            "description": "权重输入框占位符",
        },
        "save_button": {"name": "保存", "description": "保存按钮文本"},
        "cancel_button": {"name": "取消", "description": "取消按钮文本"},
        "error_title": {"name": "错误", "description": "错误消息标题"},
        "success_title": {"name": "成功", "description": "成功消息标题"},
        "info_title": {"name": "提示", "description": "信息消息标题"},
        "no_genders_error": {
            "name": "请至少输入一个权重值",
            "description": "未输入权重时的错误提示",
        },
        "invalid_weights_error": {
            "name": "以下权重包含非法字符或为保留字: {weights}",
            "description": "权重验证失败时的错误提示",
        },
        "save_error": {
            "name": "保存权重选项失败",
            "description": "保存权重选项时的错误提示",
        },
        "success_message": {
            "name": "成功创建 {count} 个新权重选项",
            "description": "成功创建权重选项时的提示消息",
        },
        "no_new_weights_message": {
            "name": "所有权重选项均已存在，未创建新的权重选项",
            "description": "没有创建新权重选项时的提示消息",
        },
        "unsaved_changes_title": {
            "name": "未保存的更改",
            "description": "未保存更改对话框标题",
        },
        "unsaved_changes_message": {
            "name": "您有未保存的更改，确定要关闭窗口吗？",
            "description": "未保存更改对话框内容",
        },
        "discard_button": {"name": "放弃更改", "description": "放弃更改按钮文本"},
        "continue_editing_button": {
            "name": "继续编辑",
            "description": "继续编辑按钮文本",
        },
        "delete_button": {"name": "删除", "description": "删除按钮文本"},
        "delete_weight_title": {
            "name": "删除权重选项",
            "description": "删除权重选项对话框标题",
        },
        "delete_weight_message": {
            "name": "确定要删除权重选项 '{weight}' 吗？此操作将删除该权重选项的所有信息，且不可恢复",
            "description": "删除权重选项确认对话框内容",
        },
        "delete_multiple_weights_title": {
            "name": "删除多个权重选项",
            "description": "删除多个权重选项对话框标题",
        },
        "delete_multiple_weights_message": {
            "name": "确定要删除以下 {count} 个权重选项吗？此操作将删除这些权重选项的所有信息，且不可恢复\n\n{weights}",
            "description": "删除多个权重选项确认对话框内容",
        },
        "delete_weight_success_title": {
            "name": "删除成功",
            "description": "删除权重选项成功通知标题",
        },
        "delete_weight_success_message": {
            "name": "成功删除 {count} 个权重选项",
            "description": "删除权重选项成功通知内容",
        },
        "delete_weight_cancel_button": {
            "name": "取消删除",
            "description": "取消删除权重选项按钮文本",
        },
        "no_deletable_weights": {
            "name": "没有可删除的权重选项",
            "description": "没有可删除权重选项时的提示",
        },
        "select_weight_to_delete": {
            "name": "请选择要删除的权重选项",
            "description": "选择删除权重选项的提示",
        },
        "select_weight_dialog_title": {
            "name": "选择要删除的权重选项",
            "description": "选择删除权重选项对话框标题",
        },
        "select_weight_dialog_message": {
            "name": "请选择要删除的权重选项：",
            "description": "选择删除权重选项对话框内容",
        },
        "delete_selected_weights_button": {
            "name": "删除选中",
            "description": "删除选中权重选项按钮文本",
        },
        "delete_weight_error": {
            "name": "删除权重选项失败: {error}",
            "description": "删除权重选项失败错误信息",
        },
        "weight_deleted_title": {
            "name": "权重选项已删除",
            "description": "删除权重选项提示标题",
        },
        "weight_deleted_message": {
            "name": "权重选项 '{weight}' 已从输入框中移除，请保存更改以永久删除",
            "description": "删除权重选项提示内容",
        },
    },
}
