import os
from datetime import datetime
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    GroupHeaderCardWidget,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    SegmentedWidget,
    SpinBox,
    SwitchButton,
    TableWidget,
    TitleLabel,
)

from app.Language.obtain_language import (
    get_any_position_value_async,
    get_content_description_async,
    get_content_name_async,
    get_content_pushbutton_name_async,
    get_content_switchbutton_name_async,
)
from app.tools.backup_utils import (
    BackupResult,
    format_size,
    get_auto_backup_interval_days,
    get_auto_backup_max_count,
    get_backup_target_defs,
    get_backup_dir,
    get_backup_dir_size_bytes,
    get_last_success_backup_text,
    list_backup_files,
    is_auto_backup_enabled,
    is_backup_target_enabled,
    create_backup,
    prune_backups,
    set_last_success_backup,
)
from app.tools.config import (
    NotificationConfig,
    NotificationType,
    import_all_data_from_file_path,
    show_notification,
)
from app.tools.personalised import get_theme_icon
from app.tools.interaction_perf import start_interaction
from app.tools.settings_access import update_settings
from app.tools.table_batching import next_request_id, run_batched


class ManualBackupWorker(QThread):
    finishedWithResult = Signal(bool, object, str)

    def run(self):
        try:
            result = create_backup(kind="manual")
            set_last_success_backup(result)
            prune_backups(get_auto_backup_max_count())
            self.finishedWithResult.emit(True, result, "")
        except Exception as e:
            logger.exception(f"手动备份失败: {e}")
            self.finishedWithResult.emit(False, None, str(e))


class _RestoreListSignals(QObject):
    loaded = Signal(int, list)
    failed = Signal(int, str)


class _RestoreListWorker(QRunnable):
    def __init__(self, request_id: int):
        super().__init__()
        self.request_id = request_id
        self.signals = _RestoreListSignals()

    def run(self):
        try:
            rows = []
            for file_path in list_backup_files():
                name = file_path.name
                try:
                    file_stat = file_path.stat()
                    try:
                        mtime_text = datetime.fromtimestamp(
                            file_stat.st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        mtime_text = "--"
                    size_text = format_size(file_stat.st_size)
                except Exception:
                    mtime_text = "--"
                    size_text = "--"

                rows.append(
                    {
                        "path": str(file_path),
                        "name": name,
                        "mtime_text": mtime_text,
                        "size_text": size_text,
                    }
                )
            self.signals.loaded.emit(self.request_id, rows)
        except Exception as e:
            logger.exception(f"加载备份列表失败: {e}")
            self.signals.failed.emit(self.request_id, str(e))


class BackupManagerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: ManualBackupWorker | None = None
        self._backup_target_switches: dict[str, SwitchButton] = {}
        self._restore_selected_file: str = ""
        self._restore_list_request_id = 0
        self._restore_rows: list[dict[str, str]] = []
        self._restore_refresh_trace = None
        self._restore_refresh_notification_mode: str | None = None
        self._init_ui()
        self._refresh_all()

    def _init_ui(self):
        self.setWindowTitle(get_content_name_async("basic_settings", "backup_manager"))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        self.title_label = TitleLabel(
            get_content_name_async("basic_settings", "backup_manager")
        )
        header_row.addWidget(self.title_label, 1)
        self.main_layout.addLayout(header_row)

        self.segment = SegmentedWidget(self)
        self.segment.addItem(
            "auto",
            get_any_position_value_async("basic_settings", "backup_tabs", "auto"),
        )
        self.segment.addItem(
            "manual",
            get_any_position_value_async("basic_settings", "backup_tabs", "manual"),
        )
        self.segment.addItem(
            "restore",
            get_any_position_value_async("basic_settings", "backup_tabs", "restore"),
        )
        self.segment.addItem(
            "content",
            get_any_position_value_async("basic_settings", "backup_tabs", "content"),
        )
        self.main_layout.addWidget(self.segment)

        self.stacked = QStackedWidget(self)
        self.main_layout.addWidget(self.stacked, 1)

        self.auto_page = QWidget(self)
        self.auto_layout = QVBoxLayout(self.auto_page)
        self.auto_layout.setContentsMargins(0, 0, 0, 0)
        self.auto_layout.setSpacing(12)
        self.auto_layout.addWidget(self._create_auto_card())
        self.auto_layout.addStretch(1)

        self.manual_page = QWidget(self)
        self.manual_layout = QVBoxLayout(self.manual_page)
        self.manual_layout.setContentsMargins(0, 0, 0, 0)
        self.manual_layout.setSpacing(12)
        self.manual_layout.addWidget(self._create_manual_card())
        self.manual_layout.addStretch(1)

        self.restore_page = QWidget(self)
        self.restore_layout = QVBoxLayout(self.restore_page)
        self.restore_layout.setContentsMargins(0, 0, 0, 0)
        self.restore_layout.setSpacing(12)
        self.restore_tip_label = BodyLabel(
            get_any_position_value_async("basic_settings", "backup_restore_tip", "text")
        )
        self.restore_tip_label.setWordWrap(True)
        self.restore_layout.addWidget(self.restore_tip_label)
        self.restore_layout.addWidget(self._create_restore_card())
        self.restore_layout.addStretch(1)

        self.content_page = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_page)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.content_tip_label = BodyLabel(
            get_any_position_value_async("basic_settings", "backup_content_tip", "text")
        )
        self.content_tip_label.setWordWrap(True)
        self.content_layout.addWidget(self.content_tip_label)
        self.content_layout.addWidget(self._create_content_card())
        self.content_layout.addStretch(1)

        self.stacked.addWidget(self.auto_page)
        self.stacked.addWidget(self.manual_page)
        self.stacked.addWidget(self.restore_page)
        self.stacked.addWidget(self.content_page)

        self.segment.currentItemChanged.connect(self._on_segment_changed)
        self.segment.setCurrentItem("auto")

    def _create_auto_card(self) -> GroupHeaderCardWidget:
        card = GroupHeaderCardWidget(self)
        card.setTitle(get_content_name_async("basic_settings", "backup_auto_settings"))
        card.setBorderRadius(8)

        self.auto_enabled_switch = SwitchButton()
        self.auto_enabled_switch.setOnText(
            get_content_switchbutton_name_async(
                "basic_settings", "backup_auto_enabled", "enable"
            )
        )
        self.auto_enabled_switch.setOffText(
            get_content_switchbutton_name_async(
                "basic_settings", "backup_auto_enabled", "disable"
            )
        )
        self.auto_enabled_switch.setChecked(is_auto_backup_enabled())
        self.auto_enabled_switch.checkedChanged.connect(self._on_auto_enabled_changed)

        self.interval_spin = SpinBox()
        self.interval_spin.setRange(1, 365)
        self.interval_spin.setFixedWidth(120)
        self.interval_spin.setValue(get_auto_backup_interval_days())
        self.interval_spin.valueChanged.connect(self._on_interval_changed)

        self.max_count_spin = SpinBox()
        self.max_count_spin.setRange(0, 512)
        self.max_count_spin.setFixedWidth(120)
        self.max_count_spin.setValue(get_auto_backup_max_count())
        self.max_count_spin.valueChanged.connect(self._on_max_count_changed)

        self.last_backup_label = BodyLabel("")
        self.last_backup_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        card.addGroup(
            get_theme_icon("ic_fluent_toggle_right_20_filled"),
            get_content_name_async("basic_settings", "backup_auto_enabled"),
            get_content_description_async("basic_settings", "backup_auto_enabled"),
            self.auto_enabled_switch,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_calendar_clock_20_filled"),
            get_content_name_async("basic_settings", "backup_auto_interval_days"),
            get_content_description_async(
                "basic_settings", "backup_auto_interval_days"
            ),
            self.interval_spin,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_number_circle_1_20_filled"),
            get_content_name_async("basic_settings", "backup_auto_max_count"),
            get_content_description_async("basic_settings", "backup_auto_max_count"),
            self.max_count_spin,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_clock_20_filled"),
            get_content_name_async("basic_settings", "backup_last_success"),
            get_content_description_async("basic_settings", "backup_last_success"),
            self.last_backup_label,
        )
        self._update_auto_controls_enabled()
        return card

    def _create_manual_card(self) -> GroupHeaderCardWidget:
        card = GroupHeaderCardWidget(self)
        card.setTitle(
            get_content_name_async("basic_settings", "backup_manual_settings")
        )
        card.setBorderRadius(8)

        self.backup_now_button = PrimaryPushButton(
            get_content_pushbutton_name_async("basic_settings", "backup_now")
        )
        self.backup_now_button.clicked.connect(self._on_backup_now_clicked)

        self.open_backup_folder_button = PushButton(
            get_content_pushbutton_name_async("basic_settings", "backup_open_folder")
        )
        self.open_backup_folder_button.clicked.connect(self._on_open_folder_clicked)

        self.backup_size_label = BodyLabel("")
        self.backup_size_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        card.addGroup(
            get_theme_icon("ic_fluent_save_20_filled"),
            get_content_name_async("basic_settings", "backup_now"),
            get_content_description_async("basic_settings", "backup_now"),
            self.backup_now_button,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_folder_open_20_filled"),
            get_content_name_async("basic_settings", "backup_open_folder"),
            get_content_description_async("basic_settings", "backup_open_folder"),
            self.open_backup_folder_button,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_storage_20_filled"),
            get_content_name_async("basic_settings", "backup_folder_size"),
            get_content_description_async("basic_settings", "backup_folder_size"),
            self.backup_size_label,
        )
        return card

    def _create_restore_card(self) -> GroupHeaderCardWidget:
        card = GroupHeaderCardWidget(self)
        card.setTitle(
            get_content_name_async("basic_settings", "backup_restore_settings")
        )
        card.setBorderRadius(8)

        self.restore_table = TableWidget()
        self.restore_table.setBorderVisible(True)
        self.restore_table.setBorderRadius(8)
        self.restore_table.setWordWrap(False)
        self.restore_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.restore_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.restore_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.restore_table.verticalHeader().hide()
        self.restore_table.setSortingEnabled(False)

        headers = get_any_position_value_async(
            "basic_settings", "backup_restore_table_headers"
        )
        if isinstance(headers, list) and len(headers) >= 4:
            self.restore_table.setColumnCount(4)
            self.restore_table.setHorizontalHeaderLabels(headers[:4])
        else:
            self.restore_table.setColumnCount(4)
            self.restore_table.setHorizontalHeaderLabels(["File", "Time", "Size", ""])
        for i in range(self.restore_table.columnCount()):
            mode = (
                QHeaderView.ResizeMode.ResizeToContents
                if i == self.restore_table.columnCount() - 1
                else QHeaderView.ResizeMode.Stretch
            )
            self.restore_table.horizontalHeader().setSectionResizeMode(i, mode)
            self.restore_table.horizontalHeader().setDefaultAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

        self.restore_refresh_button = PushButton(
            get_content_pushbutton_name_async(
                "basic_settings", "backup_restore_refresh"
            )
        )
        self.restore_refresh_button.clicked.connect(self._on_restore_refresh_clicked)

        self.restore_start_button = PrimaryPushButton(
            get_content_pushbutton_name_async("basic_settings", "backup_restore_start")
        )
        self.restore_start_button.clicked.connect(self._on_restore_start_clicked)

        card.addGroup(
            get_theme_icon("ic_fluent_folder_open_20_filled"),
            get_content_name_async("basic_settings", "backup_restore_file_list"),
            get_content_description_async("basic_settings", "backup_restore_file_list"),
            self.restore_refresh_button,
        )
        card.addGroup(
            get_theme_icon("ic_fluent_arrow_reset_20_filled"),
            get_content_name_async("basic_settings", "backup_restore_start"),
            get_content_description_async("basic_settings", "backup_restore_start"),
            self.restore_start_button,
        )
        card.layout().addWidget(self.restore_table)
        self._refresh_restore_files()
        return card

    def _create_content_card(self) -> GroupHeaderCardWidget:
        card = GroupHeaderCardWidget(self)
        card.setTitle(
            get_content_name_async("basic_settings", "backup_content_settings")
        )
        card.setBorderRadius(8)

        self._backup_target_switches.clear()
        for include_key, _dir_name, _dir_path in get_backup_target_defs():
            switch = SwitchButton()
            switch.setOnText(
                get_content_switchbutton_name_async(
                    "basic_settings", include_key, "enable"
                )
            )
            switch.setOffText(
                get_content_switchbutton_name_async(
                    "basic_settings", include_key, "disable"
                )
            )
            switch.setChecked(is_backup_target_enabled(include_key))
            switch.checkedChanged.connect(
                lambda checked, k=include_key: self._on_backup_target_changed(
                    k, checked
                )
            )
            self._backup_target_switches[include_key] = switch

            card.addGroup(
                get_theme_icon("ic_fluent_folder_open_20_filled"),
                get_content_name_async("basic_settings", include_key),
                get_content_description_async("basic_settings", include_key),
                switch,
            )

        return card

    def _on_segment_changed(self, key: str):
        if key == "manual":
            self.stacked.setCurrentWidget(self.manual_page)
            self._refresh_size()
        elif key == "restore":
            self.stacked.setCurrentWidget(self.restore_page)
            self._refresh_restore_files()
        elif key == "content":
            self.stacked.setCurrentWidget(self.content_page)
            self._refresh_backup_targets()
        else:
            self.stacked.setCurrentWidget(self.auto_page)
            self._refresh_last_backup()

    def _refresh_restore_files(self):
        trace = start_interaction("backup_manager.refresh_restore_files")
        self._restore_refresh_trace = trace
        self._restore_selected_file = ""
        self._restore_rows = []
        self.restore_table.clearSelection()
        self.restore_table.setRowCount(0)
        trace.log("first_feedback")
        request_id = next_request_id(self, "_restore_list_request_id")
        worker = _RestoreListWorker(request_id)
        worker.signals.loaded.connect(self._on_restore_files_loaded)
        worker.signals.failed.connect(self._on_restore_files_failed)
        QThreadPool.globalInstance().start(worker)

    def _render_restore_rows_batch(self, request_id: int, rows, start: int, end: int):
        if self._restore_list_request_id != request_id:
            return

        for row_index in range(start, end):
            row = rows[row_index]
            name_item = QTableWidgetItem(row["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, row["path"])
            time_item = QTableWidgetItem(row["mtime_text"])
            size_item = QTableWidgetItem(row["size_text"])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.restore_table.setItem(row_index, 0, name_item)
            self.restore_table.setItem(row_index, 1, time_item)
            self.restore_table.setItem(row_index, 2, size_item)
            delete_button = PushButton(
                get_content_pushbutton_name_async(
                    "basic_settings", "backup_restore_delete"
                )
            )
            delete_button.clicked.connect(
                lambda _checked=False, fp=row["path"]: self._on_restore_delete_clicked(
                    fp
                )
            )
            self.restore_table.setCellWidget(row_index, 3, delete_button)

    def _finish_restore_rows_render(self, request_id: int):
        if self._restore_list_request_id != request_id:
            return

        if self._restore_rows:
            self.restore_table.selectRow(0)

        if self._restore_refresh_trace is not None:
            self._restore_refresh_trace.log("data_ready")
            self._restore_refresh_trace = None

        self._show_restore_refresh_result(None, len(self._restore_rows))

    def _on_restore_files_loaded(self, request_id: int, rows: list[dict[str, str]]):
        if self._restore_list_request_id != request_id:
            return

        self._restore_rows = rows
        self.restore_table.setRowCount(len(rows))
        run_batched(
            self,
            request_id,
            rows,
            self._render_restore_rows_batch,
            batch_size=12,
            on_finish=self._finish_restore_rows_render,
            request_attr="_restore_list_request_id",
        )

    def _on_restore_files_failed(self, request_id: int, error: str):
        if self._restore_list_request_id != request_id:
            return

        self._restore_rows = []
        self.restore_table.setRowCount(0)
        if self._restore_refresh_trace is not None:
            self._restore_refresh_trace.log("data_ready")
            self._restore_refresh_trace = None
        self._show_restore_refresh_result(error, 0)

    def _show_restore_refresh_result(self, error: str | None, count: int):
        mode = self._restore_refresh_notification_mode
        self._restore_refresh_notification_mode = None
        if mode != "notify":
            return

        if error:
            show_notification(
                NotificationType.ERROR,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_restore_refresh"
                    ),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_restore_refresh_result", "failure"
                    ).format(error=error),
                ),
                parent=self.window(),
            )
            return

        if count <= 0:
            content = get_any_position_value_async(
                "basic_settings", "backup_restore_refresh_result", "empty"
            )
            show_notification(
                NotificationType.INFO,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_restore_refresh"
                    ),
                    content=str(content),
                ),
                parent=self.window(),
            )
            return

        content = get_any_position_value_async(
            "basic_settings", "backup_restore_refresh_result", "success"
        ).format(count=count)
        show_notification(
            NotificationType.SUCCESS,
            NotificationConfig(
                title=get_content_name_async(
                    "basic_settings", "backup_restore_refresh"
                ),
                content=str(content),
            ),
            parent=self.window(),
        )

    def _on_restore_delete_clicked(self, file_path: str):
        if not file_path:
            return

        dialog = MessageBox(
            get_any_position_value_async(
                "basic_settings", "backup_restore_delete_confirm", "title"
            ),
            get_any_position_value_async(
                "basic_settings", "backup_restore_delete_confirm", "content"
            ).format(file=os.path.basename(file_path)),
            self.window(),
        )
        dialog.yesButton.setText(
            get_content_pushbutton_name_async("basic_settings", "backup_restore_delete")
        )
        dialog.cancelButton.setText(
            get_content_pushbutton_name_async(
                "basic_settings", "backup_restore_delete_cancel"
            )
        )
        if not dialog.exec():
            return

        try:
            backup_dir = get_backup_dir().resolve()
            p = Path(file_path)
            try:
                resolved = p.resolve()
            except Exception:
                resolved = p

            if backup_dir not in resolved.parents:
                raise ValueError("不允许删除备份目录以外的文件")

            if resolved.suffix.lower() != ".zip":
                raise ValueError("不支持的备份文件类型")

            resolved.unlink(missing_ok=True)
            show_notification(
                NotificationType.SUCCESS,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_restore_delete"
                    ),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_restore_delete_result", "success"
                    ).format(file=resolved.name),
                ),
                parent=self.window(),
            )
        except Exception as e:
            logger.exception(f"删除备份文件失败: {e}")
            show_notification(
                NotificationType.ERROR,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_restore_delete"
                    ),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_restore_delete_result", "failure"
                    ).format(error=str(e)),
                ),
                parent=self.window(),
            )
        finally:
            self._refresh_restore_files()

    def _on_restore_refresh_clicked(self):
        self._restore_refresh_notification_mode = "notify"
        self._refresh_restore_files()

    def _get_selected_restore_file(self) -> str:
        items = self.restore_table.selectedItems()
        if not items:
            return ""
        try:
            p = items[0].data(Qt.ItemDataRole.UserRole)
            return "" if p is None else str(p)
        except Exception:
            return ""

    def _on_restore_start_clicked(self):
        file_path = self._get_selected_restore_file()
        if not file_path:
            show_notification(
                NotificationType.WARNING,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_restore_start"
                    ),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_restore_no_selection", "text"
                    ),
                ),
                parent=self.window(),
            )
            return

        dialog = MessageBox(
            get_any_position_value_async(
                "basic_settings", "backup_restore_confirm", "title"
            ),
            get_any_position_value_async(
                "basic_settings", "backup_restore_confirm", "content"
            ).format(file=os.path.basename(file_path)),
            self.window(),
        )
        dialog.yesButton.setText(
            get_any_position_value_async(
                "basic_settings", "backup_restore_confirm", "confirm_button"
            )
        )
        dialog.cancelButton.setText(
            get_any_position_value_async(
                "basic_settings", "backup_restore_confirm", "cancel_button"
            )
        )
        if not dialog.exec():
            return

        import_all_data_from_file_path(file_path, parent=self.window())

    def _refresh_backup_targets(self):
        for include_key, switch in self._backup_target_switches.items():
            try:
                switch.blockSignals(True)
                switch.setChecked(is_backup_target_enabled(include_key))
            finally:
                switch.blockSignals(False)

    def _on_backup_target_changed(self, include_key: str, checked: bool):
        update_settings("backup", include_key, bool(checked))

    def _update_auto_controls_enabled(self):
        enabled = self.auto_enabled_switch.isChecked()
        self.interval_spin.setEnabled(enabled)
        self.max_count_spin.setEnabled(enabled)

    def _on_auto_enabled_changed(self, checked: bool):
        update_settings("backup", "auto_backup_enabled", checked)
        self._update_auto_controls_enabled()

    def _on_interval_changed(self, value: int):
        update_settings("backup", "auto_backup_interval_days", int(value))

    def _on_max_count_changed(self, value: int):
        update_settings("backup", "auto_backup_max_count", int(value))
        try:
            prune_backups(int(value))
            self._refresh_size()
        except Exception:
            pass

    def _refresh_last_backup(self):
        text = get_last_success_backup_text()
        if not text:
            self.last_backup_label.setText(
                get_any_position_value_async(
                    "basic_settings", "backup_last_success_text", "none"
                )
            )
        else:
            self.last_backup_label.setText(text)

    def _refresh_size(self):
        try:
            size = get_backup_dir_size_bytes()
            self.backup_size_label.setText(format_size(size))
        except Exception:
            self.backup_size_label.setText("--")

    def _refresh_all(self):
        self._refresh_last_backup()
        self._refresh_size()
        self._refresh_backup_targets()
        if hasattr(self, "restore_table"):
            self._refresh_restore_files()

    def _on_open_folder_clicked(self):
        try:
            backup_dir = get_backup_dir()
            os.startfile(str(backup_dir))
        except Exception as e:
            logger.exception(f"打开备份文件夹失败: {e}")
            show_notification(
                NotificationType.ERROR,
                NotificationConfig(
                    title=get_content_name_async(
                        "basic_settings", "backup_open_folder"
                    ),
                    content=str(e),
                ),
                parent=self.window(),
            )

    def _on_backup_now_clicked(self):
        if self._worker and self._worker.isRunning():
            return
        self.backup_now_button.setEnabled(False)
        self.open_backup_folder_button.setEnabled(False)
        self._worker = ManualBackupWorker()
        self._worker.finishedWithResult.connect(self._on_manual_backup_finished)
        self._worker.start()

    def _on_manual_backup_finished(self, ok: bool, result_obj: object, error: str):
        self.backup_now_button.setEnabled(True)
        self.open_backup_folder_button.setEnabled(True)

        if ok and isinstance(result_obj, BackupResult):
            show_notification(
                NotificationType.SUCCESS,
                NotificationConfig(
                    title=get_content_name_async("basic_settings", "backup_now"),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_now_result", "success"
                    ).format(path=str(result_obj.file_path)),
                ),
                parent=self.window(),
            )
        else:
            show_notification(
                NotificationType.ERROR,
                NotificationConfig(
                    title=get_content_name_async("basic_settings", "backup_now"),
                    content=get_any_position_value_async(
                        "basic_settings", "backup_now_result", "failure"
                    ).format(error=error or ""),
                ),
                parent=self.window(),
            )

        self._refresh_all()

    def closeEvent(self, event):  # type: ignore[override]
        try:
            if self._worker is not None:
                try:
                    self._worker.finishedWithResult.disconnect(
                        self._on_manual_backup_finished
                    )
                except Exception:
                    pass
                try:
                    self._worker.finished.connect(self._worker.deleteLater)
                except Exception:
                    pass
                self._worker = None
        except Exception:
            pass
        super().closeEvent(event)
