from loguru import logger
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *
from qfluentwidgets import *

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.personalised import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.tools.interaction_perf import start_interaction
from app.Language.obtain_language import *
from app.common.history import *
from app.common.history.background_loader import build_roll_call_history_payload


class _HistoryLoadSignals(QObject):
    loaded = Signal(int, object)
    failed = Signal(int, str)


class _HistoryLoadWorker(QRunnable):
    def __init__(self, request_id: int, build_payload):
        super().__init__()
        self.request_id = request_id
        self._build_payload = build_payload
        self.signals = _HistoryLoadSignals()

    def run(self):
        try:
            payload = self._build_payload()
            self.signals.loaded.emit(self.request_id, payload)
        except Exception as e:
            logger.exception(f"点名历史后台加载失败: {e}")
            self.signals.failed.emit(self.request_id, str(e))


# ==================================================
# 点名历史记录表格
# ==================================================
class roll_call_history_table(GroupHeaderCardWidget):
    """点名历史记录表格卡片"""

    refresh_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setTitle(get_content_name_async("roll_call_history_table", "title"))
        self.setBorderRadius(8)

        # 初始化数据加载器
        class_history = get_all_history_names("roll_call")
        self.data_loader = None
        self.current_class_name = class_history[0] if class_history else ""
        self.current_mode = 0
        self.current_subject = ""  # 当前选择的课程
        self.batch_size = 30  # 每次加载的行数
        self.current_row = 0  # 当前加载到的行数
        self.total_rows = 0  # 总行数
        self.is_loading = False  # 是否正在加载数据
        self.has_class_record = False  # 是否有课程记录
        self.available_subjects = []  # 可用的课程列表
        self.force_load_all = False
        self._history_request_id = 0
        self._cached_row_models = []
        self._active_refresh_worker = None
        self._history_has_gender = False
        self._history_has_group = False
        self._refresh_debounce_timer = QTimer(self)
        self._refresh_debounce_timer.setSingleShot(True)
        self._refresh_debounce_timer.timeout.connect(self.refresh_data)
        self._directory_refresh_timer = QTimer(self)
        self._directory_refresh_timer.setSingleShot(True)
        self._directory_refresh_timer.timeout.connect(self.refresh_class_history)

        # 创建班级选择区域
        QTimer.singleShot(APPLY_DELAY, self.create_class_selection)

        # 创建表格区域
        QTimer.singleShot(APPLY_DELAY, self.create_table)

        # 初始化班级列表
        QTimer.singleShot(APPLY_DELAY, self.refresh_class_history)

        # 设置文件系统监视器
        QTimer.singleShot(APPLY_DELAY, self.setup_file_watcher)

        # 初始化数据
        QTimer.singleShot(APPLY_DELAY, self.schedule_refresh_data)

        # 连接信号
        self.refresh_signal.connect(self.schedule_refresh_data)

    def create_class_selection(self):
        """创建班级选择区域"""
        self.class_comboBox = ComboBox()

        # 获取班级历史列表并填充下拉框
        class_history = get_all_history_names("roll_call")
        self.class_comboBox.addItems(class_history)

        # 设置默认选择
        if class_history:
            saved_name = str(
                get_settings_snapshot()
                .get("roll_call_history_table", {})
                .get("select_class_name", "")
                or ""
            )
            selected_index = (
                class_history.index(saved_name) if saved_name in class_history else 0
            )
            self.class_comboBox.setCurrentIndex(selected_index)
            self.current_class_name = class_history[selected_index]
        else:
            # 如果没有班级历史，设置占位符
            self.class_comboBox.setCurrentIndex(-1)
            self.class_comboBox.setPlaceholderText(
                get_content_name_async("roll_call_history_table", "select_class_name")
            )
            self.current_class_name = ""

        self.class_comboBox.currentIndexChanged.connect(self.on_class_changed)
        self.class_comboBox.currentTextChanged.connect(
            lambda: self.on_class_changed(-1)
        )

        # 选择查看模式
        self.all_names = get_all_names("roll_call", self.class_comboBox.currentText())
        self.mode_comboBox = ComboBox()
        self.mode_comboBox.addItems(
            get_content_combo_name_async("roll_call_history_table", "select_mode")
            + self.all_names
        )
        self.mode_comboBox.setCurrentIndex(0)
        self.mode_comboBox.currentIndexChanged.connect(self.schedule_refresh_data)

        # 选择课程
        self.subject_comboBox = ComboBox()
        self.subject_comboBox.addItems(
            get_content_combo_name_async("roll_call_history_table", "select_subject")
        )
        self.subject_comboBox.setCurrentIndex(0)
        self.subject_comboBox.currentIndexChanged.connect(self.on_subject_changed)

        self.addGroup(
            get_theme_icon("ic_fluent_class_20_filled"),
            get_content_name_async("roll_call_history_table", "select_class_name"),
            get_content_description_async(
                "roll_call_history_table", "select_class_name"
            ),
            self.class_comboBox,
        )

        # 创建一个容器来放置查看模式和课程选择下拉框
        self.mode_subject_widget = QWidget()
        mode_subject_layout = QHBoxLayout(self.mode_subject_widget)
        mode_subject_layout.setContentsMargins(0, 0, 0, 0)
        mode_subject_layout.setSpacing(10)
        mode_subject_layout.addWidget(self.mode_comboBox)
        mode_subject_layout.addWidget(self.subject_comboBox)

        self.addGroup(
            get_theme_icon("ic_fluent_reading_mode_mobile_20_filled"),
            get_content_name_async("roll_call_history_table", "select_mode"),
            get_content_description_async("roll_call_history_table", "select_mode"),
            self.mode_subject_widget,
        )

    def create_table(self):
        """创建表格区域"""
        # 创建表格
        self.table = TableWidget()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 暂时禁用排序，在数据加载完成后再启用
        self.table.setSortingEnabled(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().hide()

        # 初始化排序状态
        self.sort_column = -1
        self.sort_order = Qt.SortOrder.AscendingOrder

        # 根据当前选择的模式设置表格头
        self.update_table_headers()

        # 设置表格属性
        for i in range(self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.Stretch
            )
            self.table.horizontalHeader().setDefaultAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.table.horizontalHeader().setSectionsClickable(True)

        # 初始状态下不显示排序指示器
        self.table.horizontalHeader().setSortIndicatorShown(False)

        # 连接滚动事件，用于分段加载
        self.table.verticalScrollBar().valueChanged.connect(self._on_scroll)

        # 连接排序信号，在排序时重新加载数据
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        self.layout().addWidget(self.table)

    def _on_scroll(self, value):
        """处理表格滚动事件，实现分段加载

        Args:
            value: 滚动条当前位置
        """
        # 如果正在加载或没有更多数据，直接返回
        if self.is_loading or self.current_row >= self.total_rows:
            return

        # 获取滚动条最大值和当前值
        max_value = self.table.verticalScrollBar().maximum()
        current_value = self.table.verticalScrollBar().value()

        # 使用更精确的滚动检测，确保在滚动到底部时触发
        scroll_threshold = max(20, max_value * 0.1)  # 至少20像素或10%的位置
        if current_value >= max_value - scroll_threshold:
            self._load_more_data()

    def _ensure_scrollable_rows(self):
        if not hasattr(self, "table"):
            return
        if self.current_row >= self.total_rows:
            return
        max_value = self.table.verticalScrollBar().maximum()
        attempts = 0
        while self.current_row < self.total_rows and max_value == 0 and attempts < 20:
            self._load_more_data()
            max_value = self.table.verticalScrollBar().maximum()
            attempts += 1

    def _on_header_clicked(self, column):
        """处理表头点击事件，实现排序

        Args:
            column: 被点击的列索引
        """
        # 如果正在加载数据，不处理排序
        if self.is_loading:
            return

        # 获取当前排序状态，优先使用我们自己的状态变量
        current_sort_column = self.sort_column if self.sort_column >= 0 else -1
        current_sort_order = (
            self.sort_order if self.sort_column >= 0 else Qt.SortOrder.AscendingOrder
        )

        # 如果点击的是同一列，则切换排序顺序；否则设置为升序
        if column == current_sort_column:
            # 切换排序顺序
            if current_sort_order == Qt.SortOrder.AscendingOrder:
                new_sort_order = Qt.SortOrder.DescendingOrder
            else:
                new_sort_order = Qt.SortOrder.AscendingOrder
        else:
            # 点击不同列，设置为升序
            new_sort_order = Qt.SortOrder.AscendingOrder

        # 更新排序状态
        self.sort_column = column
        self.sort_order = new_sort_order

        # 设置排序指示器
        self.table.horizontalHeader().setSortIndicator(column, new_sort_order)
        self.table.horizontalHeader().setSortIndicatorShown(True)

        self.force_load_all = True

        # 重置数据加载状态
        self.current_row = 0
        self.table.setRowCount(0)
        self.refresh_data()

    def _sort_current_data(self):
        """对已加载的数据进行排序，不重新加载数据"""
        # 获取当前表格中的所有数据
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            table_data.append(row_data)

        # 如果没有数据，直接返回
        if not table_data:
            return

        # 根据排序状态对数据进行排序
        def sort_key(row):
            # 尝试将数据转换为数字，如果失败则使用字符串比较
            try:
                # 对于权重列，需要特殊处理
                # 在模式0（学生数据）中：
                #   - 有课程时：权重列索引为6
                #   - 无课程时：权重列索引为5
                # 在模式1（会话数据）中：
                #   - 有课程时：权重列索引为6
                #   - 无课程时：权重列索引为5
                # 在模式2（统计数据）中：
                #   - 有课程时：权重列索引为6
                #   - 无课程时：权重列索引为5
                if self.current_mode == 0:
                    # 模式0：学生数据
                    if self.sort_column == 5:
                        # 列5可能是课程或权重
                        if self.has_class_record:
                            # 有课程，列5是课程，列6是权重
                            return row[self.sort_column]
                        else:
                            # 无课程，列5是权重
                            weight_str = row[self.sort_column]
                            weight_str = weight_str.lstrip("0")
                            if not weight_str:
                                return 0.0
                            return float(weight_str)
                    elif self.sort_column == 6 and self.has_class_record:
                        # 有课程时，列6是权重
                        weight_str = row[self.sort_column]
                        weight_str = weight_str.lstrip("0")
                        if not weight_str:
                            return 0.0
                        return float(weight_str)
                elif self.current_mode in [1, 2]:
                    # 模式1和2：会话数据和统计数据
                    if self.sort_column == 5:
                        # 有课程，列5是课程
                        return row[self.sort_column]
                    elif self.sort_column == 6 and self.has_class_record:
                        # 有课程时，列6是权重
                        weight_str = row[self.sort_column]
                        weight_str = weight_str.lstrip("0")
                        if not weight_str:
                            return 0.0
                        return float(weight_str)
                return float(row[self.sort_column])
            except (ValueError, IndexError):
                return row[self.sort_column]

        # 应用排序
        reverse_order = self.sort_order == Qt.SortOrder.DescendingOrder
        table_data.sort(key=sort_key, reverse=reverse_order)

        # 清空表格
        self.table.setRowCount(0)

        # 重新填充排序后的数据
        self.table.setRowCount(len(table_data))
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_data in enumerate(row_data):
                item = create_table_item(cell_data)
                self.table.setItem(row_idx, col_idx, item)

    def _load_more_data(self):
        """加载更多数据"""
        if self.is_loading or self.current_row >= self.total_rows:
            return

        self.is_loading = True
        try:
            new_row_count = min(self.current_row + self.batch_size, self.total_rows)
            self.table.setRowCount(new_row_count)

            for row in range(self.current_row, new_row_count):
                if row >= len(self._cached_row_models):
                    break
                row_data = self._cached_row_models[row]
                for col, cell in enumerate(row_data):
                    self.table.setItem(row, col, create_table_item(cell))

            self.current_row = new_row_count
            if self.current_row >= self.total_rows:
                self.table.setSortingEnabled(True)
                if self.sort_column >= 0:
                    self.table.horizontalHeader().setSortIndicator(
                        self.sort_column, self.sort_order
                    )
                    self.table.horizontalHeader().setSortIndicatorShown(True)
        finally:
            self.is_loading = False

    def setup_file_watcher(self):
        """设置文件系统监视器，监控班级历史记录文件夹的变化"""
        roll_call_history_dir = get_data_path("history/roll_call_history")
        if not roll_call_history_dir.exists():
            logger.warning(f"班级历史记录文件夹不存在: {roll_call_history_dir}")
            return
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.addPath(str(roll_call_history_dir))
        self.file_watcher.directoryChanged.connect(self.on_directory_changed)
        # logger.debug(f"已设置文件监视器，监控目录: {roll_call_history_dir}")

    def on_directory_changed(self, path):
        """当目录内容发生变化时调用此方法

        Args:
            path: 发生变化的目录路径
        """
        # logger.debug(f"检测到目录变化: {path}")
        self._directory_refresh_timer.start(250)

    def refresh_class_history(self):
        """刷新班级下拉框列表"""
        if not hasattr(self, "class_comboBox"):
            return

        # 保存当前选择的班级名称和索引
        current_class_name = self.class_comboBox.currentText()
        current_index = self.class_comboBox.currentIndex()

        # 获取最新的班级历史列表
        class_history = get_all_history_names("roll_call")

        # 清空并重新填充下拉框
        self.class_comboBox.blockSignals(True)
        self.class_comboBox.clear()
        self.class_comboBox.addItems(class_history)

        # 如果之前选择的班级还在列表中，则重新选择它
        if current_class_name and current_class_name in class_history:
            index = class_history.index(current_class_name)
            self.class_comboBox.setCurrentIndex(index)
            # 更新current_class_name
            self.current_class_name = current_class_name
        elif (
            class_history and current_index >= 0 and current_index < len(class_history)
        ):
            # 如果之前选择的索引仍然有效，使用相同的索引
            self.class_comboBox.setCurrentIndex(current_index)
            # 更新current_class_name
            self.current_class_name = class_history[current_index]
        elif class_history:
            # 如果之前选择的班级不在列表中，选择第一个班级
            self.class_comboBox.setCurrentIndex(0)
            # 更新current_class_name
            self.current_class_name = class_history[0]
        else:
            # 如果没有班级历史，设置占位符
            self.class_comboBox.setCurrentIndex(-1)
            self.class_comboBox.setPlaceholderText(
                get_content_name_async("roll_call_history_table", "select_class_name")
            )
            # 更新current_class_name
            self.current_class_name = ""
        self.class_comboBox.blockSignals(False)

        if hasattr(self, "clear_button"):
            self.clear_button.setEnabled(bool(self.current_class_name))
        self._update_mode_options()
        self.schedule_refresh_data()

    def on_class_changed(self, index):
        """班级选择变化时刷新表格数据"""
        if not hasattr(self, "class_comboBox"):
            return

        # 启用或禁用清除按钮
        if hasattr(self, "clear_button"):
            self.clear_button.setEnabled(self.class_comboBox.currentIndex() >= 0)

        # 更新当前班级名称
        self.current_class_name = self.class_comboBox.currentText()
        self._update_mode_options()

        # 刷新表格数据
        self.schedule_refresh_data()

    def on_subject_changed(self, index):
        """课程选择变化时刷新表格数据"""
        if not hasattr(self, "subject_comboBox"):
            return

        # 获取选择的课程
        if index == 0:
            self.current_subject = ""
        else:
            self.current_subject = self.subject_comboBox.currentText()

        # 刷新表格数据
        self.schedule_refresh_data()

    def schedule_refresh_data(self):
        if not hasattr(self, "_refresh_debounce_timer"):
            return
        self._refresh_debounce_timer.start(0)

    def _update_mode_options(self, names=None):
        if not hasattr(self, "mode_comboBox"):
            return
        current_text = self.mode_comboBox.currentText()
        options = (
            list(names)
            if names is not None
            else get_all_names("roll_call", self.class_comboBox.currentText())
        )
        self.all_names = options
        items = get_content_combo_name_async("roll_call_history_table", "select_mode")
        self.mode_comboBox.blockSignals(True)
        self.mode_comboBox.clear()
        self.mode_comboBox.addItems(items + options)
        idx = self.mode_comboBox.findText(current_text)
        self.mode_comboBox.setCurrentIndex(idx if idx >= 0 else 0)
        self.mode_comboBox.blockSignals(False)

    def _apply_subject_options(self, subjects):
        self.available_subjects = list(subjects)
        if not hasattr(self, "subject_comboBox"):
            return
        current_subject = self.current_subject
        self.subject_comboBox.blockSignals(True)
        self.subject_comboBox.clear()
        self.subject_comboBox.addItems(
            get_content_combo_name_async("roll_call_history_table", "select_subject")
            + self.available_subjects
        )
        if current_subject:
            idx = self.subject_comboBox.findText(current_subject)
            self.subject_comboBox.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            self.subject_comboBox.setCurrentIndex(0)
        self.subject_comboBox.blockSignals(False)
        self.subject_comboBox.setVisible(bool(self.available_subjects))

    def _apply_refresh_payload(self, request_id, payload):
        if request_id != self._history_request_id:
            return

        self._active_refresh_worker = None
        trace = getattr(self, "_refresh_trace", None)
        self.has_class_record = bool(payload.has_class_record)
        self._history_has_gender = bool(payload.has_gender)
        self._history_has_group = bool(payload.has_group)
        self._cached_row_models = list(payload.rows)
        self.total_rows = len(self._cached_row_models)
        self.current_row = 0

        self._update_mode_options(payload.all_names)
        self._apply_subject_options(payload.available_subjects)
        self.update_table_headers()
        self.table.setRowCount(0)

        if self.total_rows:
            initial_rows = (
                self.total_rows
                if self.force_load_all
                else min(self.batch_size, self.total_rows)
            )
            self.table.setRowCount(initial_rows)
            self._load_more_data()
            self._ensure_scrollable_rows()
        else:
            self.table.setSortingEnabled(False)

        self.force_load_all = False
        if trace is not None:
            trace.log("data_ready")

    def _handle_refresh_failed(self, request_id, error_message):
        if request_id != self._history_request_id:
            return
        self._active_refresh_worker = None
        logger.error(f"点名历史刷新失败: {error_message}")
        self.force_load_all = False
        trace = getattr(self, "_refresh_trace", None)
        if trace is not None:
            trace.log("data_ready")

    def refresh_data(self):
        """刷新表格数据"""
        trace = start_interaction("roll_call_history.refresh")
        self._refresh_trace = trace
        if not hasattr(self, "table"):
            trace.log("data_ready")
            return
        if not hasattr(self, "class_comboBox"):
            trace.log("data_ready")
            return
        class_name = self.class_comboBox.currentText()
        if not class_name:
            self.table.setRowCount(0)
            trace.log("first_feedback")
            trace.log("data_ready")
            return
        self.current_class_name = class_name

        # 重置课程记录标志
        self.has_class_record = False

        self.update_table_headers()

        # 重置数据加载状态
        self.current_row = 0
        self.is_loading = False
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        trace.log("first_feedback")
        self._history_request_id += 1
        request_id = self._history_request_id
        self.current_mode = (
            self.mode_comboBox.currentIndex() if hasattr(self, "mode_comboBox") else 0
        )
        settings_snapshot = get_settings_snapshot()
        selected_name = (
            self.mode_comboBox.currentText()
            if self.current_mode >= 2 and hasattr(self, "mode_comboBox")
            else settings_snapshot.get("roll_call_history_table", {}).get(
                "select_student_name"
            )
        )

        worker = _HistoryLoadWorker(
            request_id,
            lambda: build_roll_call_history_payload(
                class_name,
                self.current_mode,
                self.current_subject,
                str(selected_name or ""),
                self.sort_column,
                self.sort_order == Qt.SortOrder.DescendingOrder,
            ),
        )
        worker.signals.loaded.connect(self._apply_refresh_payload)
        worker.signals.failed.connect(self._handle_refresh_failed)
        self._active_refresh_worker = worker
        QThreadPool.globalInstance().start(worker)

    def update_table_headers(self):
        """更新表格标题"""
        if not hasattr(self, "table"):
            return

        if hasattr(self, "mode_comboBox"):
            self.current_mode = self.mode_comboBox.currentIndex()
        else:
            self.current_mode = 0

        has_gender = bool(getattr(self, "_history_has_gender", False))
        has_group = bool(getattr(self, "_history_has_group", False))

        if self.current_mode == 0:
            headers = get_content_name_async(
                "roll_call_history_table", "HeaderLabels_all_weight"
            )
        elif self.current_mode == 1:
            headers = get_content_name_async(
                "roll_call_history_table", "HeaderLabels_time_weight"
            )
        else:
            headers = get_content_name_async(
                "roll_call_history_table", "HeaderLabels_Individual_weight"
            )

        if self.current_mode == 0:
            if not has_gender and not has_group:
                headers = headers[:2] + headers[4:]
            elif not has_gender:
                headers = headers[:2] + headers[3:]
            elif not has_group:
                headers = headers[:3] + headers[4:]
        elif self.current_mode == 1:
            if not has_gender and not has_group:
                headers = headers[:2] + headers[4:]
            elif not has_gender:
                headers = headers[:2] + headers[3:]
            elif not has_group:
                headers = headers[:3] + headers[4:]
            if not self.has_class_record:
                headers = headers[:-2] + headers[-1:]
        elif self.current_mode >= 2:
            if not has_gender and not has_group:
                headers = headers[:3] + headers[5:]
            elif not has_gender:
                headers = headers[:3] + headers[4:]
            elif not has_group:
                headers = headers[:4] + headers[5:]
            if not self.has_class_record:
                headers = headers[:-2] + headers[-1:]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
