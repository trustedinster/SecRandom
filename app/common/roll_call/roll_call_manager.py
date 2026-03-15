from PySide6.QtCore import (
    QObject,
    Signal,
    QTimer,
    QEasingCurve,
    QFileSystemWatcher,
    QThreadPool,
    QRunnable,
    Qt,
)
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel
from dataclasses import dataclass
from loguru import logger
from random import SystemRandom

from app.common.data.list import (
    get_student_list,
    filter_students_data,
    get_group_list,
    get_gender_list,
    get_class_name_list,
)
from app.common.display.result_display import ResultDisplayUtils
from app.common.history import calculate_weight
from app.common.roll_call.roll_call_utils import RollCallUtils
from app.common.music.music_player import music_player
from app.common.behind_scenes.behind_scenes_utils import BehindScenesUtils
from app.common.voice.voice import TTSHandler
from app.common.extraction.extract import _is_non_class_time
from app.page_building.another_window import create_remaining_list_window
from app.tools.config import remove_record
from app.tools.interaction_perf import start_interaction
from app.tools.settings_access import get_settings_signals, readme_settings_async
from app.tools.list_specific_settings_access import read_roll_call_setting
from app.tools.personalised import load_custom_font
from app.Language.obtain_language import (
    get_content_pushbutton_name_async,
    get_content_combo_name_async,
)
from app.tools.path_utils import get_data_path
from app.tools.variable import APP_INIT_DELAY
from app.tools.config import track_event
from app.common.safety.verify_proxy import require_and_run_lazy

system_random = SystemRandom()


@dataclass(frozen=True, slots=True)
class RollCallDrawContext:
    class_name: str
    group_filter: str
    gender_filter: str
    group_index: int
    gender_index: int
    half_repeat: int


@dataclass(frozen=True, slots=True)
class RollCallDrawPlan:
    animation: int
    autoplay_count: int
    animation_interval: int
    animation_music: str | None
    result_music: str | None


@dataclass(frozen=True, slots=True)
class RollCallPreparedState:
    context: RollCallDrawContext
    plan: RollCallDrawPlan
    students: list[tuple]
    tags_by_id: dict[int, list[str]]
    weights: list[float]


class RollCallManager(QObject):
    """
    点名业务逻辑管理器
    负责数据加载、随机抽取、结果处理等非UI逻辑
    """

    # 信号定义
    data_loaded = Signal(bool)  # 数据加载完成信号
    error_occurred = Signal(str)  # 错误信号

    def __init__(self, settings_group="roll_call_settings"):
        super().__init__()
        self.students = []
        self.tags_by_id = {}
        self.weights = []
        self.current_class_name = ""
        self.current_group_filter = ""
        self.current_gender_filter = ""
        self.current_group_index = 0
        self.current_gender_index = 0
        self.half_repeat = 0
        self.settings_group = settings_group
        self._precomputed_result = None
        self._precompute_key = None
        self._precompute_running = False
        self._settings_version = 0
        self._draw_data_cache = {}
        self._count_summary_cache = {}
        self._option_cache = {}
        self._display_settings_cache = None
        self._display_settings_cache_version = -1
        self._prepare_request_id = 0
        try:
            get_settings_signals().settingChanged.connect(self._on_setting_changed)
        except Exception:
            pass

    def _on_setting_changed(self, *_):
        self._settings_version += 1
        self.invalidate_derived_cache()

    def invalidate_derived_cache(self) -> None:
        self._draw_data_cache.clear()
        self._count_summary_cache.clear()
        self._option_cache.clear()
        self._display_settings_cache = None
        self._display_settings_cache_version = -1
        self._precomputed_result = None
        self._precompute_key = None
        self._precompute_running = False

    def _build_draw_data_cache_key(
        self,
        class_name,
        group_filter,
        gender_filter,
        group_index,
        gender_index,
        half_repeat,
    ):
        return (
            class_name,
            group_filter,
            gender_filter,
            int(group_index or 0),
            int(gender_index or 0),
            int(half_repeat or 0),
            self._settings_version,
        )

    def get_group_options(self, class_name: str) -> list[str]:
        cache_key = ("groups", class_name, self._settings_version)
        cached = self._option_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        groups = tuple(get_group_list(class_name))
        self._option_cache[cache_key] = groups
        return list(groups)

    def get_gender_options(self, class_name: str) -> list[str]:
        cache_key = ("genders", class_name, self._settings_version)
        cached = self._option_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        genders = tuple(get_gender_list(class_name))
        self._option_cache[cache_key] = genders
        return list(genders)

    def get_display_settings(self, refresh: bool = False):
        if (
            refresh
            or self._display_settings_cache is None
            or self._display_settings_cache_version != self._settings_version
        ):
            self._display_settings_cache = RollCallUtils.create_display_settings(
                self.settings_group
            )
            self._display_settings_cache_version = self._settings_version
        return dict(self._display_settings_cache or {})

    def get_total_count(
        self, class_name: str, group_index: int, group_filter: str
    ) -> int:
        cache_key = (
            "total",
            class_name,
            int(group_index or 0),
            group_filter,
            self._settings_version,
        )
        cached = self._count_summary_cache.get(cache_key)
        if isinstance(cached, int):
            return cached
        total_count = RollCallUtils.get_total_count(
            class_name, group_index, group_filter
        )
        total_count = int(total_count or 0)
        self._count_summary_cache[cache_key] = total_count
        return total_count

    def get_many_count_summary(
        self,
        class_name: str,
        group_index: int,
        group_filter: str,
        gender_filter: str,
        half_repeat: int,
    ) -> tuple[int, int, str]:
        display_mode = readme_settings_async(
            "page_management", "roll_call_quantity_label"
        )
        cache_key = (
            "many",
            class_name,
            int(group_index or 0),
            group_filter,
            gender_filter,
            int(half_repeat or 0),
            int(display_mode or 0),
            self._settings_version,
        )
        cached = self._count_summary_cache.get(cache_key)
        if isinstance(cached, tuple) and len(cached) == 3:
            return cached
        summary = RollCallUtils.update_many_count_label_text(
            class_name,
            group_index,
            group_filter,
            gender_filter,
            half_repeat,
            display_mode=display_mode,
        )
        self._count_summary_cache[cache_key] = summary
        return summary

    def _create_draw_plan(self, class_name: str) -> RollCallDrawPlan:
        animation = read_roll_call_setting(class_name, "animation")
        autoplay_count = read_roll_call_setting(class_name, "autoplay_count")
        animation_interval = read_roll_call_setting(class_name, "animation_interval")
        animation_music = read_roll_call_setting(class_name, "animation_music")
        result_music = read_roll_call_setting(class_name, "result_music")

        try:
            animation = int(animation or 0)
        except Exception:
            animation = 0

        try:
            autoplay_count = int(autoplay_count or 0)
        except Exception:
            autoplay_count = 0

        try:
            animation_interval = int(animation_interval or 0)
        except Exception:
            animation_interval = 0

        return RollCallDrawPlan(
            animation=animation,
            autoplay_count=autoplay_count,
            animation_interval=animation_interval,
            animation_music=animation_music or None,
            result_music=result_music or None,
        )

    def build_draw_context(
        self,
        class_name: str,
        group_filter: str,
        gender_filter: str,
        group_index: int,
        gender_index: int,
        half_repeat: int,
    ) -> RollCallDrawContext:
        try:
            half_repeat = int(half_repeat or 0)
        except Exception:
            half_repeat = 0

        return RollCallDrawContext(
            class_name=class_name,
            group_filter=group_filter,
            gender_filter=gender_filter,
            group_index=group_index,
            gender_index=gender_index,
            half_repeat=half_repeat,
        )

    def prepare_draw(self, context: RollCallDrawContext) -> RollCallDrawPlan:
        self.load_data(
            context.class_name,
            context.group_filter,
            context.gender_filter,
            context.group_index,
            context.gender_index,
            context.half_repeat,
        )
        return self._create_draw_plan(context.class_name)

    def prepare_draw_async(self, context: RollCallDrawContext, on_ready, on_error=None):
        self._prepare_request_id += 1
        request_id = self._prepare_request_id
        cache_key = self._build_draw_data_cache_key(
            context.class_name,
            context.group_filter,
            context.gender_filter,
            context.group_index,
            context.gender_index,
            context.half_repeat,
        )
        cached = self._draw_data_cache.get(cache_key)
        if isinstance(cached, dict):
            self.current_class_name = context.class_name
            self.current_group_filter = context.group_filter
            self.current_gender_filter = context.gender_filter
            self.current_group_index = context.group_index
            self.current_gender_index = context.gender_index
            self.half_repeat = context.half_repeat
            self.students = list(cached.get("students") or [])
            self.tags_by_id = dict(cached.get("tags_by_id") or {})
            self.weights = list(cached.get("weights") or [])
            try:
                on_ready(
                    RollCallPreparedState(
                        context=context,
                        plan=self._create_draw_plan(context.class_name),
                        students=list(self.students),
                        tags_by_id=dict(self.tags_by_id),
                        weights=list(self.weights),
                    )
                )
            except Exception as e:
                if callable(on_error):
                    on_error(str(e))
            return request_id

        class _Signals(QObject):
            finished = Signal(int, object)
            failed = Signal(int, str)

        class _Worker(QRunnable):
            def __init__(self, fn, signals):
                super().__init__()
                self.fn = fn
                self.signals = signals

            def run(self):
                try:
                    self.signals.finished.emit(request_id, self.fn())
                except Exception as e:
                    logger.exception(f"点名抽取准备失败: {e}")
                    self.signals.failed.emit(request_id, str(e))

        def _prepare():
            raw_students = get_student_list(context.class_name)
            tags_by_id = {}
            for student in raw_students or []:
                if not isinstance(student, dict):
                    continue
                try:
                    sid = int(student.get("id", 0) or 0)
                except Exception:
                    sid = 0
                if sid <= 0:
                    continue
                tags_by_id[sid] = student.get("tags") or []

            students = filter_students_data(
                raw_students,
                context.group_index,
                context.group_filter,
                context.gender_index,
                context.gender_filter,
            )
            weighted_students = calculate_weight(
                [
                    {
                        "id": s[0],
                        "name": s[1],
                        "gender": s[2],
                        "group": s[3],
                        "exist": s[4],
                    }
                    for s in students
                ],
                context.class_name,
            )
            weights = [item.get("next_weight", 1.0) for item in weighted_students]
            return RollCallPreparedState(
                context=context,
                plan=self._create_draw_plan(context.class_name),
                students=list(students),
                tags_by_id=tags_by_id,
                weights=weights,
            )

        def _handle_finished(finished_request_id, prepared_state):
            if finished_request_id != self._prepare_request_id:
                return
            prepared_state = prepared_state
            self.current_class_name = prepared_state.context.class_name
            self.current_group_filter = prepared_state.context.group_filter
            self.current_gender_filter = prepared_state.context.gender_filter
            self.current_group_index = prepared_state.context.group_index
            self.current_gender_index = prepared_state.context.gender_index
            self.half_repeat = prepared_state.context.half_repeat
            self.students = list(prepared_state.students)
            self.tags_by_id = dict(prepared_state.tags_by_id)
            self.weights = list(prepared_state.weights)
            self._draw_data_cache[cache_key] = {
                "students": list(self.students),
                "tags_by_id": dict(self.tags_by_id),
                "weights": list(self.weights),
            }
            on_ready(prepared_state)

        def _handle_failed(failed_request_id, message):
            if failed_request_id != self._prepare_request_id:
                return
            if callable(on_error):
                on_error(message)

        signals = _Signals()
        signals.finished.connect(_handle_finished)
        signals.failed.connect(_handle_failed)
        QThreadPool.globalInstance().start(_Worker(_prepare, signals))
        return request_id

    def finalize_draw(self, count: int, *, parent=None):
        result = self.draw_final_students(count)
        if isinstance(result, dict) and result.get("reset_required"):
            RollCallUtils.reset_drawn_records(
                parent,
                self.current_class_name,
                self.current_gender_filter,
                self.current_group_filter,
            )
            self.invalidate_derived_cache()
            return {"reset_required": True, "class_name": self.current_class_name}

        selected_students = (result or {}).get("selected_students") or []
        selected_students_dict = (result or {}).get("selected_students_dict") or []
        self.save_result(selected_students, selected_students_dict)
        self.invalidate_derived_cache()

        result = dict(result or {})
        result["should_update_remaining"] = bool(
            self.half_repeat and self.half_repeat > 0
        )
        return result

    def reset_records_with_notification(self, *, parent=None):
        RollCallUtils.reset_drawn_records(
            parent,
            self.current_class_name,
            self.current_gender_filter,
            self.current_group_filter,
        )
        self.invalidate_derived_cache()

    def load_data(
        self,
        class_name,
        group_filter,
        gender_filter,
        group_index,
        gender_index,
        half_repeat,
    ):
        """
        加载学生数据
        """
        try:
            self.current_class_name = class_name
            self.current_group_filter = group_filter
            self.current_gender_filter = gender_filter
            self.current_group_index = group_index
            self.current_gender_index = gender_index
            self.half_repeat = half_repeat

            cache_key = self._build_draw_data_cache_key(
                class_name,
                group_filter,
                gender_filter,
                group_index,
                gender_index,
                half_repeat,
            )
            cached = self._draw_data_cache.get(cache_key)
            if isinstance(cached, dict):
                self.students = list(cached.get("students") or [])
                self.tags_by_id = dict(cached.get("tags_by_id") or {})
                self.weights = list(cached.get("weights") or [])
                logger.debug(
                    f"点名抽取数据命中缓存: class={class_name}, group={group_filter}, gender={gender_filter}"
                )
                self.data_loaded.emit(True)
                return True

            # 获取原始学生列表
            raw_students = get_student_list(class_name)

            tags_by_id = {}
            for s in raw_students or []:
                if not isinstance(s, dict):
                    continue
                try:
                    sid = int(s.get("id", 0) or 0)
                except Exception:
                    sid = 0
                if sid <= 0:
                    continue
                tags_by_id[sid] = s.get("tags") or []
            self.tags_by_id = tags_by_id

            # 过滤数据
            self.students = filter_students_data(
                raw_students, group_index, group_filter, gender_index, gender_filter
            )

            # 计算权重
            self.weights = self._calculate_weights()
            self._draw_data_cache[cache_key] = {
                "students": list(self.students),
                "tags_by_id": dict(self.tags_by_id),
                "weights": list(self.weights),
            }

            logger.info(f"加载 {len(self.students)} 个学生在这个班级 {class_name}")
            self.data_loaded.emit(True)
            return True

        except Exception as e:
            logger.exception(f"加载学生数据时出错: {e}")
            self.error_occurred.emit(str(e))
            self.data_loaded.emit(False)
            return False

    def _calculate_weights(self):
        """计算权重"""
        # 转换 self.students (tuples) 为 dict list 以适配 calculate_weight
        students_dicts = []
        for s in self.students:
            students_dicts.append(
                {"id": s[0], "name": s[1], "gender": s[2], "group": s[3], "exist": s[4]}
            )

        # 批量计算权重
        weighted_students = calculate_weight(students_dicts, self.current_class_name)

        # 提取权重值，保持顺序一致
        weights = []
        for s in weighted_students:
            weights.append(s.get("next_weight", 1.0))

        return weights

    def get_random_students(self, count):
        """
        获取随机学生列表（用于动画帧）
        """
        if not self.students:
            return []

        # 如果需要抽取的数量大于学生总数，允许重复
        allow_repeat = count > len(self.students)

        selected = []
        if allow_repeat:
            # 简单的随机选择用于动画效果
            selected = [system_random.choice(self.students) for _ in range(count)]
        else:
            # 简单的随机选择用于动画效果（无权重）
            # 注意：权重采样(without replacement)比较复杂且对动画效果影响不大，
            # 这里直接使用均匀分布采样以保证性能和避免重复
            selected = system_random.sample(self.students, k=count)

        return selected

    def draw_final_students(self, count):
        """
        执行最终抽取
        """
        precomputed = self.take_precomputed_result(count)
        if precomputed:
            return precomputed
        # 使用RollCallUtils中的核心抽取逻辑，它处理了去重、权重等复杂逻辑
        result = RollCallUtils.draw_random_students(
            self.current_class_name,
            self.current_group_index,
            self.current_group_filter,
            self.current_gender_index,
            self.current_gender_filter,
            count,
            self.half_repeat,
            settings_group=self.settings_group,
        )
        return result

    def save_result(self, selected_students, selected_students_dict):
        """
        保存抽取结果
        """
        return RollCallUtils.record_drawn_students(
            self.current_class_name,
            selected_students,
            selected_students_dict,
            self.current_gender_filter,
            self.current_group_filter,
            self.half_repeat,
        )

    def _build_precompute_key(self, count):
        try:
            count = int(count or 0)
        except Exception:
            count = 0
        return (
            self.current_class_name,
            self.current_group_filter,
            self.current_gender_filter,
            self.current_group_index,
            self.current_gender_index,
            self.half_repeat,
            count,
        )

    def start_precompute_final(self, count):
        try:
            count = int(count or 0)
        except Exception:
            count = 0
        if count <= 0 or not self.current_class_name:
            return
        key = self._build_precompute_key(count)
        if self._precompute_running and self._precompute_key == key:
            return
        self._precompute_key = key
        self._precomputed_result = None
        self._precompute_running = True

        class_name = self.current_class_name
        group_index = self.current_group_index
        group_filter = self.current_group_filter
        gender_index = self.current_gender_index
        gender_filter = self.current_gender_filter
        half_repeat = self.half_repeat
        draw_count = count

        class _Signals(QObject):
            loaded = Signal(object, object)

        class _Loader(QRunnable):
            def __init__(self, fn, signals, key):
                super().__init__()
                self.fn = fn
                self.signals = signals
                self.key = key

            def run(self):
                try:
                    result = self.fn()
                    self.signals.loaded.emit(self.key, result)
                except Exception as e:
                    logger.exception(f"预计算最终抽取结果失败: {e}")

        def _collect():
            return RollCallUtils.draw_random_students(
                class_name,
                group_index,
                group_filter,
                gender_index,
                gender_filter,
                draw_count,
                half_repeat,
                settings_group=self.settings_group,
            )

        signals = _Signals()
        signals.loaded.connect(self._on_precompute_loaded)
        runnable = _Loader(_collect, signals, key)
        QThreadPool.globalInstance().start(runnable)

    def _on_precompute_loaded(self, key, result):
        if key != self._precompute_key:
            return
        self._precomputed_result = result
        self._precompute_running = False

    def take_precomputed_result(self, count):
        key = self._build_precompute_key(count)
        if self._precomputed_result and self._precompute_key == key:
            result = self._precomputed_result
            self._precomputed_result = None
            self._precompute_running = False
            return result
        return None

    def reset_records(self):
        """重置抽取记录"""
        remove_record(
            self.current_class_name,
            self.current_gender_filter,
            self.current_group_filter,
        )


def start_roll_call_draw(widget):
    trace = start_interaction("roll_call.draw")
    track_event("roll_call_draw")
    if getattr(widget, "_draw_prepare_in_progress", False):
        trace.log("ignored_while_preparing")
        return

    manager = widget.manager
    class_name = widget.list_combobox.currentText()
    group_filter = widget.range_combobox.currentText()
    gender_filter = widget.gender_combobox.currentText()
    group_index = widget.range_combobox.currentIndex()
    gender_index = widget.gender_combobox.currentIndex()
    half_repeat = read_roll_call_setting(class_name, "half_repeat")

    context = manager.build_draw_context(
        class_name,
        group_filter,
        gender_filter,
        group_index,
        gender_index,
        half_repeat,
    )
    trace.log("context_ready")
    _set_roll_call_prepare_state(widget, True)
    widget.start_button.setText("准备中...")
    _show_roll_call_loading_placeholder(widget, "正在准备抽取数据...")
    trace.log("loading_visible")

    def _ready(prepared_state: RollCallPreparedState):
        _set_roll_call_prepare_state(widget, False)
        widget._draw_plan = prepared_state.plan
        trace.log("prepare_ready")
        _begin_roll_call_draw(widget, trace=trace)

    def _failed(message: str):
        _set_roll_call_prepare_state(widget, False)
        widget.start_button.setText(
            get_content_pushbutton_name_async("roll_call", "start_button")
        )
        widget.start_button.setEnabled(True)
        _show_roll_call_loading_placeholder(
            widget, f"抽取准备失败: {message or '未知错误'}"
        )
        trace.log("prepare_failed")

    manager.prepare_draw_async(context, on_ready=_ready, on_error=_failed)


def init_file_watcher(widget):
    widget.file_watcher = QFileSystemWatcher()
    setup_file_watcher(widget)


def init_long_press(widget):
    widget.press_timer = QTimer()
    widget.press_timer.timeout.connect(widget.handle_long_press)
    widget.long_press_interval = 100
    widget.long_press_delay = 500
    widget.is_long_pressing = False
    widget.long_press_direction = 0


def init_tts(widget):
    widget.tts_handler = TTSHandler()


def init_animation_state(widget):
    widget.is_animating = False
    widget._draw_plan = None
    widget._draw_prepare_in_progress = False


def _show_roll_call_loading_placeholder(widget, text: str):
    try:
        ResultDisplayUtils.clear_grid(widget.result_grid)
    except Exception:
        pass

    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setObjectName("rollCallLoadingLabel")
    if hasattr(widget, "_set_widget_font"):
        try:
            widget._set_widget_font(label, 14)
        except Exception:
            pass
    widget.result_grid.addWidget(label)


def _set_roll_call_prepare_state(widget, preparing: bool):
    widget._draw_prepare_in_progress = preparing
    for attr_name in (
        "start_button",
        "reset_button",
        "minus_button",
        "plus_button",
        "list_combobox",
        "range_combobox",
        "gender_combobox",
        "remaining_button",
    ):
        control = getattr(widget, attr_name, None)
        if control is None:
            continue
        try:
            if attr_name == "start_button":
                control.setEnabled(not preparing)
                continue
            control.setEnabled(not preparing)
        except Exception:
            pass


def _begin_roll_call_draw(widget, trace=None):
    widget._cached_display_dict = widget.manager.get_display_settings(refresh=False)
    widget._cached_animation_widgets = None
    widget._cached_show_random = widget._cached_display_dict.get("show_random", 0)

    widget.start_button.setText(
        get_content_pushbutton_name_async("roll_call", "start_button")
    )
    widget.start_button.setEnabled(True)
    try:
        widget.start_button.clicked.disconnect()
    except Exception as e:
        logger.exception("Error disconnecting start_button clicked (ignored): {}", e)

    widget.draw_random()
    if trace is not None:
        trace.log("first_feedback_ready")

    plan = widget._draw_plan
    animation = plan.animation if plan else 0
    autoplay_count = plan.autoplay_count if plan else 0
    animation_interval = plan.animation_interval if plan else 0
    animation_music = plan.animation_music if plan else None
    if animation in [0, 1]:
        widget.manager.start_precompute_final(widget.current_count)

    if animation == 0:
        if animation_music:
            music_player.play_music(
                music_file=animation_music,
                settings_group="roll_call_settings",
                loop=True,
                fade_in=True,
            )
        widget.start_button.setText(
            get_content_pushbutton_name_async("roll_call", "stop_button")
        )
        widget.is_animating = True
        widget.animation_timer = QTimer()
        widget.animation_timer.timeout.connect(widget.animate_result)
        widget.animation_timer.start(animation_interval)
        widget.start_button.clicked.connect(lambda: widget.stop_animation())
    elif animation == 1:
        if animation_music:
            music_player.play_music(
                music_file=animation_music,
                settings_group="roll_call_settings",
                loop=True,
                fade_in=True,
            )
        widget.is_animating = True
        widget.animation_timer = QTimer()
        widget.animation_timer.timeout.connect(widget.animate_result)
        widget.animation_timer.start(animation_interval)
        widget.start_button.setEnabled(False)
        QTimer.singleShot(
            autoplay_count * animation_interval,
            lambda: [
                widget.animation_timer.stop(),
                widget.stop_animation(),
                widget.start_button.setEnabled(True),
            ],
        )
        widget.start_button.clicked.connect(lambda: widget.start_draw())
    elif animation == 2:
        widget.stop_animation()
        widget.start_button.clicked.connect(lambda: widget.start_draw())


def handle_long_press(widget):
    if widget.is_long_pressing:
        widget.press_timer.setInterval(widget.long_press_interval)
        widget.update_count(widget.long_press_direction)


def start_long_press(widget, direction):
    widget.long_press_direction = direction
    widget.is_long_pressing = True
    widget.press_timer.setInterval(widget.long_press_delay)
    widget.press_timer.start()


def stop_long_press(widget):
    widget.is_long_pressing = False
    widget.press_timer.stop()


def start_draw(widget):
    if _is_non_class_time():
        if readme_settings_async("linkage_settings", "verification_required"):
            logger.info("当前时间在非上课时间段内，需要密码验证")
            require_and_run_lazy(
                "roll_call_start", widget, lambda: start_roll_call_draw(widget)
            )
        else:
            logger.info("当前时间在非上课时间段内，禁止抽取")
            return
    else:
        start_roll_call_draw(widget)


def animate_result(widget):
    widget.draw_random()


def reset_count(widget):
    if _is_non_class_time():
        if readme_settings_async("linkage_settings", "verification_required"):
            logger.info("当前时间在非上课时间段内，需要密码验证")
            require_and_run_lazy("roll_call_reset", widget, widget._do_reset_count)
        else:
            logger.info("当前时间在非上课时间段内，禁止重置")
            return
    else:
        widget._do_reset_count()


def stop_animation(widget):
    is_quick_draw = hasattr(widget, "is_quick_draw") and widget.is_quick_draw
    if hasattr(widget, "animation_timer") and widget.animation_timer.isActive():
        widget.animation_timer.stop()
    widget.start_button.setText(
        get_content_pushbutton_name_async("roll_call", "start_button")
    )
    widget.is_animating = False
    widget._cached_animation_widgets = None
    widget._cached_display_dict = None
    BehindScenesUtils.clear_cache()
    try:
        widget.start_button.clicked.disconnect()
    except Exception as e:
        logger.exception(
            "Error disconnecting start_button clicked during stop_animation (ignored): {}",
            e,
        )
    widget.start_button.clicked.connect(lambda: widget.start_draw())

    result = widget.manager.finalize_draw(widget.current_count, parent=widget)
    if isinstance(result, dict) and result.get("reset_required"):
        update_many_count_label(widget)
        if (
            hasattr(widget, "remaining_list_page")
            and widget.remaining_list_page is not None
            and hasattr(widget.remaining_list_page, "count_changed")
        ):
            widget.remaining_list_page.count_changed.emit(widget.remaining_count)
        QTimer.singleShot(
            APP_INIT_DELAY, lambda: _update_remaining_list_delayed(widget)
        )
        return

    widget.final_selected_students = result.get("selected_students") or []
    widget.final_class_name = (
        result.get("class_name") or widget.manager.current_class_name
    )
    widget.final_selected_students_dict = result.get("selected_students_dict") or []
    widget.final_ipc_selected_students = result.get("ipc_selected_students") or []
    widget.final_group_filter = (
        result.get("group_filter") or widget.range_combobox.currentText()
    )
    widget.final_gender_filter = (
        result.get("gender_filter") or widget.gender_combobox.currentText()
    )

    if result.get("should_update_remaining"):
        update_many_count_label(widget)
        if (
            hasattr(widget, "remaining_list_page")
            and widget.remaining_list_page is not None
            and hasattr(widget.remaining_list_page, "count_changed")
        ):
            widget.remaining_list_page.count_changed.emit(widget.remaining_count)
        QTimer.singleShot(
            APP_INIT_DELAY, lambda: _update_remaining_list_delayed(widget)
        )

    if hasattr(widget, "final_selected_students"):
        if not is_quick_draw:
            actual_draw_count = (
                len(widget.final_selected_students)
                if widget.final_selected_students
                else 0
            )
            if actual_draw_count <= 0:
                actual_draw_count = widget.current_count
            display_result(
                widget,
                widget.final_selected_students,
                widget.final_class_name,
                draw_count=actual_draw_count,
                selected_students_dict=getattr(
                    widget, "final_selected_students_dict", None
                ),
            )
            RollCallUtils.show_notification_if_enabled(
                class_name=widget.final_class_name,
                selected_students=widget.final_selected_students,
                draw_count=actual_draw_count,
                settings_group="roll_call_notification_settings",
                ipc_selected_students=getattr(
                    widget, "final_ipc_selected_students", None
                ),
            )

        play_voice_result(widget)
        music_player.stop_music(fade_out=True)

        plan = widget._draw_plan
        result_music = plan.result_music if plan else None
        if result_music:
            music_player.play_music(
                music_file=result_music,
                settings_group="roll_call_settings",
                loop=False,
                fade_in=True,
            )


def play_voice_result(widget):
    try:
        voice_settings = {
            "voice_volume": readme_settings_async(
                "basic_voice_settings", "volume_size"
            ),
            "voice_speed": readme_settings_async("basic_voice_settings", "speech_rate"),
            "system_voice_name": readme_settings_async(
                "basic_voice_settings", "system_voice_name"
            ),
        }

        student_names = [name[1] for name in widget.final_selected_students]
        voice_engine = readme_settings_async("basic_voice_settings", "voice_engine")
        engine_type = 1 if voice_engine == "Edge TTS" else 0
        edge_tts_voice_name = readme_settings_async(
            "basic_voice_settings", "edge_tts_voice_name"
        )

        class_name = (
            widget.final_class_name
            if hasattr(widget, "final_class_name") and widget.final_class_name
            else widget.list_combobox.currentText()
        )

        widget.tts_handler.voice_play(
            config=voice_settings,
            student_names=student_names,
            engine_type=engine_type,
            voice_name=edge_tts_voice_name,
            class_name=class_name,
        )
    except Exception as e:
        logger.exception(f"播放语音失败: {e}", exc_info=True)


def draw_random(widget):
    if widget.is_animating:
        display_count = widget.current_count
        try:
            remaining_count = int(getattr(widget, "remaining_count", 0) or 0)
        except Exception:
            remaining_count = 0
        if remaining_count > 0:
            display_count = min(display_count, remaining_count)

        students = widget.manager.get_random_students(display_count)
        selected_students = []
        selected_students_dict = []
        weight_by_identity = {}
        for student, weight in zip(
            widget.manager.students or [],
            widget.manager.weights or [],
            strict=False,
        ):
            if len(student) < 2:
                continue
            weight_by_identity[(student[0], student[1])] = weight
        for s in students:
            exist = s[4] if len(s) > 4 else True
            selected_students.append((s[0], s[1], exist))
            try:
                sid = int(s[0] or 0)
            except Exception:
                sid = 0
            selected_students_dict.append(
                {
                    "id": sid,
                    "name": s[1],
                    "exist": exist,
                    "tags": (widget.manager.tags_by_id or {}).get(sid, []),
                    "next_weight": weight_by_identity.get((s[0], s[1])),
                }
            )

        display_result_animated(
            widget,
            selected_students,
            widget.manager.current_class_name,
            draw_count=display_count,
            selected_students_dict=selected_students_dict,
        )


def display_result(
    widget,
    selected_students,
    class_name,
    display_settings=None,
    draw_count=None,
    selected_students_dict=None,
):
    group_index = widget.range_combobox.currentIndex()
    settings_group = "quick_draw_settings" if display_settings else "roll_call_settings"
    if draw_count is None:
        draw_count = widget.current_count

    RollCallUtils.display_result(
        result_grid=widget.result_grid,
        class_name=class_name,
        selected_students=selected_students,
        draw_count=draw_count,
        group_index=group_index,
        settings_group=settings_group,
        display_settings=display_settings,
        selected_students_dict=selected_students_dict,
    )


def display_result_animated(
    widget, selected_students, class_name, draw_count=None, selected_students_dict=None
):
    group_index = widget.range_combobox.currentIndex()
    if draw_count is None:
        draw_count = widget.current_count

    if group_index == 1:
        show_random = getattr(widget, "_cached_show_random", 0)
        selected_students = RollCallUtils.render_group_display_students(
            class_name, selected_students, show_random
        )
        selected_students_dict = None

    cached_widgets = getattr(widget, "_cached_animation_widgets", None)
    cached_count = len(cached_widgets) if cached_widgets else 0
    current_count = len(selected_students) if selected_students else 0

    display_dict = getattr(widget, "_cached_display_dict", None)
    if display_dict is None:
        display_dict = RollCallUtils.create_display_settings("roll_call_settings")
        widget._cached_display_dict = display_dict

    if cached_widgets and cached_count == current_count and current_count > 0:
        new_texts = []
        new_colors = []
        font_size = display_dict.get("font_size", 50)
        animation_color = display_dict.get("animation_color", 0)
        display_format = display_dict.get("display_format", 0)

        for item in selected_students:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                student_id = str(item[0]) if item[0] is not None else ""
                name = str(item[1])
            else:
                student_id = ""
                name = str(item)

            from app.common.display.result_display import (
                STUDENT_ID_FORMAT,
                NAME_SPACING,
            )

            student_id_str = (
                STUDENT_ID_FORMAT.format(num=student_id) if student_id else ""
            )

            formatted_name = (
                f"{name[0]}{NAME_SPACING}{name[1]}"
                if len(name) == 2 and group_index == 0
                else name
            )

            if display_format == 1:
                text = formatted_name
            elif display_format == 2:
                text = student_id_str if student_id_str else formatted_name
            else:
                if draw_count == 1:
                    text = (
                        f"{student_id_str}\n{formatted_name}"
                        if student_id_str
                        else formatted_name
                    )
                else:
                    text = (
                        f"{student_id_str} {formatted_name}"
                        if student_id_str
                        else formatted_name
                    )
            new_texts.append(text)

            if animation_color == 1:
                color = ResultDisplayUtils._generate_vibrant_color()
            elif animation_color == 2:
                fixed_color = display_dict.get("animation_fixed_color", "#000000")
                color = fixed_color
            else:
                from app.tools.personalised import is_dark_theme
                from qfluentwidgets import qconfig

                color = "#ffffff" if is_dark_theme(qconfig) else "#000000"
            new_colors.append(color)

        updated = ResultDisplayUtils.update_animation_labels_fast(
            cached_widgets, new_texts, new_colors, font_size, "roll_call_settings"
        )
        if updated:
            return

    student_labels = ResultDisplayUtils.create_student_label(
        class_name=class_name,
        selected_students=selected_students,
        selected_students_dict=selected_students_dict,
        draw_count=draw_count,
        font_size=display_dict["font_size"],
        animation_color=display_dict["animation_color"],
        display_format=display_dict["display_format"],
        display_style=display_dict["display_style"],
        show_student_image=display_dict["show_student_image"],
        group_index=group_index,
        show_random=display_dict["show_random"],
        settings_group="roll_call_settings",
        show_tags=bool(display_dict.get("show_tags")),
    )

    if cached_widgets and cached_count == current_count:
        updated = ResultDisplayUtils.update_grid_labels(
            widget.result_grid, student_labels, cached_widgets
        )
        if updated:
            ResultDisplayUtils.dispose_widgets(student_labels)
            widget._cached_animation_widgets = cached_widgets
            return

    ResultDisplayUtils.display_results_in_grid(widget.result_grid, student_labels)
    widget._cached_animation_widgets = student_labels

    widget._cached_show_random = display_dict.get("show_random", 0)

    RollCallUtils.show_notification_if_enabled(
        class_name=class_name,
        selected_students=selected_students,
        draw_count=widget.current_count,
        settings_group="roll_call_notification_settings",
        is_animating=True,
    )


def do_reset_count(widget):
    widget.current_count = 1
    widget.count_label.setText("1")
    widget.minus_button.setEnabled(False)
    widget.plus_button.setEnabled(True)
    class_name = widget.list_combobox.currentText()
    gender = widget.gender_combobox.currentText()
    group = widget.range_combobox.currentText()
    half_repeat = read_roll_call_setting(class_name, "half_repeat")
    context = widget.manager.build_draw_context(
        class_name,
        group,
        gender,
        widget.range_combobox.currentIndex(),
        widget.gender_combobox.currentIndex(),
        half_repeat,
    )
    widget.manager.load_data(
        context.class_name,
        context.group_filter,
        context.gender_filter,
        context.group_index,
        context.gender_index,
        context.half_repeat,
    )
    widget.manager.reset_records_with_notification(parent=widget)

    widget.clear_result()
    update_many_count_label(widget)

    if (
        hasattr(widget, "remaining_list_page")
        and widget.remaining_list_page is not None
    ):
        QTimer.singleShot(
            APP_INIT_DELAY, lambda: _update_remaining_list_delayed(widget)
        )

    if (
        hasattr(widget, "remaining_list_page")
        and widget.remaining_list_page is not None
        and hasattr(widget.remaining_list_page, "count_changed")
    ):
        widget.remaining_list_page.count_changed.emit(widget.remaining_count)


def update_count(widget, change):
    try:
        widget.total_count = widget.manager.get_total_count(
            widget.list_combobox.currentText(),
            widget.range_combobox.currentIndex(),
            widget.range_combobox.currentText(),
        )
        widget.current_count = max(1, int(widget.count_label.text()) + change)
        widget.count_label.setText(str(widget.current_count))
        widget.minus_button.setEnabled(widget.current_count > 1)
        widget.plus_button.setEnabled(widget.current_count < widget.total_count)
    except (ValueError, TypeError):
        widget.count_label.setText("1")
        widget.minus_button.setEnabled(False)
        widget.plus_button.setEnabled(True)


def get_total_count(widget):
    return widget.manager.get_total_count(
        widget.list_combobox.currentText(),
        widget.range_combobox.currentIndex(),
        widget.range_combobox.currentText(),
    )


def update_many_count_label(widget):
    total_count, remaining_count, formatted_text = (
        widget.manager.get_many_count_summary(
            widget.list_combobox.currentText(),
            widget.range_combobox.currentIndex(),
            widget.range_combobox.currentText(),
            widget.gender_combobox.currentText(),
            read_roll_call_setting(widget.list_combobox.currentText(), "half_repeat"),
        )
    )

    widget.remaining_count = remaining_count
    widget.many_count_label.setText(formatted_text)
    RollCallUtils.update_start_button_state(widget.start_button, total_count)


def update_remaining_list_window(widget):
    if (
        hasattr(widget, "remaining_list_page")
        and widget.remaining_list_page is not None
    ):
        try:
            class_name = widget.list_combobox.currentText()
            group_filter = widget.range_combobox.currentText()
            gender_filter = widget.gender_combobox.currentText()
            group_index = widget.range_combobox.currentIndex()
            gender_index = widget.gender_combobox.currentIndex()
            half_repeat = read_roll_call_setting(class_name, "half_repeat")

            if hasattr(widget.remaining_list_page, "update_remaining_list"):
                widget.remaining_list_page.update_remaining_list(
                    class_name,
                    group_filter,
                    gender_filter,
                    half_repeat,
                    group_index,
                    gender_index,
                    emit_signal=False,
                    source="roll_call",
                )
        except Exception as e:
            logger.exception(f"更新剩余名单窗口内容失败: {e}")


def show_remaining_list(widget):
    if (
        hasattr(widget, "remaining_list_page")
        and widget.remaining_list_page is not None
    ):
        try:
            window = widget.remaining_list_page.window()
            if window is not None:
                window.raise_()
                window.activateWindow()
                update_remaining_list_window(widget)
                return
        except Exception as e:
            logger.exception(f"激活剩余名单窗口失败: {e}")

    class_name = widget.list_combobox.currentText()
    group_filter = widget.range_combobox.currentText()
    gender_filter = widget.gender_combobox.currentText()
    group_index = widget.range_combobox.currentIndex()
    gender_index = widget.gender_combobox.currentIndex()
    half_repeat = read_roll_call_setting(class_name, "half_repeat")

    window, get_page = create_remaining_list_window(
        class_name,
        group_filter,
        gender_filter,
        half_repeat,
        group_index,
        gender_index,
        "roll_call",
    )

    def on_page_ready(page):
        widget.remaining_list_page = page
        if page and hasattr(page, "count_changed"):
            page.count_changed.connect(widget.update_many_count_label)
            widget.update_many_count_label()

    get_page(on_page_ready)
    window.windowClosed.connect(lambda: setattr(widget, "remaining_list_page", None))
    window.show()


def setup_file_watcher(widget):
    try:
        list_dir = get_data_path("list", "roll_call_list")
        if not list_dir.exists():
            list_dir.mkdir(parents=True, exist_ok=True)
        widget.file_watcher.addPath(str(list_dir))
        widget.file_watcher.directoryChanged.connect(widget.on_directory_changed)
        widget.file_watcher.fileChanged.connect(widget.on_file_changed)
    except Exception as e:
        logger.exception(f"设置文件监控器失败: {e}")


def on_directory_changed(widget, path):
    try:
        widget.manager.invalidate_derived_cache()
        QTimer.singleShot(500, lambda: refresh_class_list(widget))
    except Exception as e:
        logger.exception(f"处理文件夹变化事件失败: {e}")


def on_file_changed(widget, path):
    try:
        widget.manager.invalidate_derived_cache()
        QTimer.singleShot(500, lambda: refresh_class_list(widget))
    except Exception as e:
        logger.exception(f"处理文件变化事件失败: {e}")


def refresh_class_list(widget):
    try:
        widget.manager.invalidate_derived_cache()
        current_class = widget.list_combobox.currentText()
        new_class_list = get_class_name_list()
        widget.list_combobox.blockSignals(True)
        widget.list_combobox.clear()
        widget.list_combobox.addItems(new_class_list)

        if current_class in new_class_list:
            index = widget.list_combobox.findText(current_class)
            if index >= 0:
                widget.list_combobox.setCurrentIndex(index)
        elif new_class_list:
            widget.list_combobox.setCurrentIndex(0)

        widget.list_combobox.blockSignals(False)
        on_class_changed(widget)
    except Exception as e:
        logger.exception(f"刷新班级列表失败: {e}")


def populate_lists(widget):
    try:
        _populate_class_list(widget)
        _populate_range_combobox(widget)
        _populate_gender_combobox(widget)
        _update_count_label(widget)
        widget._adjustControlWidgetWidths()
    except Exception as e:
        logger.exception(f"延迟填充列表失败: {e}")


def _populate_class_list(widget):
    class_list = get_class_name_list()
    widget.list_combobox.blockSignals(True)
    widget.list_combobox.clear()
    if class_list:
        widget.list_combobox.addItems(class_list)
        default_class = readme_settings_async("roll_call_settings", "default_class")
        if default_class and default_class in class_list:
            index = class_list.index(default_class)
            widget.list_combobox.setCurrentIndex(index)
            logger.debug(f"应用默认抽取名单: {default_class}")
        else:
            widget.list_combobox.setCurrentIndex(0)
    widget.list_combobox.blockSignals(False)


def _populate_range_combobox(widget):
    widget.range_combobox.blockSignals(True)
    widget.range_combobox.clear()

    base_options = get_content_combo_name_async("roll_call", "range_combobox")
    group_list = widget.manager.get_group_options(widget.list_combobox.currentText())

    if group_list:
        widget.range_combobox.addItems(base_options + group_list)
    else:
        widget.range_combobox.addItems(base_options[:1])

    widget.range_combobox.blockSignals(False)


def _populate_gender_combobox(widget):
    widget.gender_combobox.blockSignals(True)
    widget.gender_combobox.clear()
    widget.gender_combobox.addItems(
        get_content_combo_name_async("roll_call", "gender_combobox")
        + widget.manager.get_gender_options(widget.list_combobox.currentText())
    )
    widget.gender_combobox.blockSignals(False)


def _update_count_label(widget):
    total_count, remaining_count, formatted_text = (
        widget.manager.get_many_count_summary(
            widget.list_combobox.currentText(),
            widget.range_combobox.currentIndex(),
            widget.range_combobox.currentText(),
            widget.gender_combobox.currentText(),
            read_roll_call_setting(widget.list_combobox.currentText(), "half_repeat"),
        )
    )

    widget.remaining_count = remaining_count
    widget.many_count_label.setText(formatted_text)
    RollCallUtils.update_start_button_state(widget.start_button, total_count)


def setup_settings_listener(widget):
    from app.tools.settings_access import get_settings_signals

    settings_signals = get_settings_signals()
    settings_signals.settingChanged.connect(widget.onSettingsChanged)


def on_settings_changed(widget, first_level_key, second_level_key, value):
    widget.manager.invalidate_derived_cache()
    if first_level_key == "roll_call_settings" and second_level_key in (
        "result_flow_animation_duration",
        "result_flow_animation_style",
    ):
        try:
            if hasattr(widget, "result_grid") and widget.result_grid is not None:
                widget.result_grid.setAnimation(
                    readme_settings_async(
                        "roll_call_settings", "result_flow_animation_duration"
                    ),
                    QEasingCurve.OutQuad,
                )
                widget.result_grid.setAnimationStyle(
                    readme_settings_async(
                        "roll_call_settings", "result_flow_animation_style"
                    )
                )
        except Exception as e:
            logger.exception(f"更新结果布局动画设置失败: {e}")

    if first_level_key == "page_management" and second_level_key.startswith(
        "roll_call"
    ):
        widget.updateUI()
        widget.settingsChanged.emit()


def set_widget_font(widget, font_size):
    try:
        if not isinstance(font_size, (int, float)):
            font_size = int(font_size) if str(font_size).isdigit() else 12
        font_size = int(font_size)
        if font_size <= 0:
            font_size = 12
        custom_font = load_custom_font()
        if custom_font:
            widget.setFont(QFont(custom_font, font_size))
    except (ValueError, TypeError) as e:
        logger.warning(f"设置字体大小失败，使用默认值: {e}")
        custom_font = load_custom_font()
        if custom_font:
            widget.setFont(QFont(custom_font, 12))


def on_class_changed(widget):
    trace = start_interaction("roll_call.class_changed")
    widget.range_combobox.blockSignals(True)
    widget.gender_combobox.blockSignals(True)
    try:
        _update_range_options(widget)
        _update_gender_options(widget)
        update_many_count_label(widget)
        _update_start_button_state(widget)
        _update_remaining_list_window(widget)
        trace.log("ui_updated")
    except Exception as e:
        logger.exception(f"切换班级时发生错误: {e}")
    finally:
        widget.range_combobox.blockSignals(False)
        widget.gender_combobox.blockSignals(False)


def on_filter_changed(widget):
    trace = start_interaction("roll_call.filter_changed")
    try:
        update_many_count_label(widget)
        _update_start_button_state(widget)
        _update_remaining_list_window(widget)
        trace.log("ui_updated")
    except Exception as e:
        logger.exception(f"切换筛选条件时发生错误: {e}")


def _update_range_options(widget):
    widget.range_combobox.clear()
    base_options = get_content_combo_name_async("roll_call", "range_combobox")
    group_list = widget.manager.get_group_options(widget.list_combobox.currentText())
    if group_list and group_list != [""]:
        widget.range_combobox.addItems(base_options + group_list)
    else:
        widget.range_combobox.addItems(base_options[:1])


def _update_gender_options(widget):
    widget.gender_combobox.clear()
    gender_options = get_content_combo_name_async("roll_call", "gender_combobox")
    gender_list = widget.manager.get_gender_options(widget.list_combobox.currentText())
    if gender_list and gender_list != [""]:
        widget.gender_combobox.addItems(gender_options + gender_list)
    else:
        widget.gender_combobox.addItems(gender_options[:1])


def _update_start_button_state(widget):
    total_count = widget.manager.get_total_count(
        widget.list_combobox.currentText(),
        widget.range_combobox.currentIndex(),
        widget.range_combobox.currentText(),
    )
    RollCallUtils.update_start_button_state(widget.start_button, total_count)


def _update_remaining_list_window(widget):
    if (
        hasattr(widget, "remaining_list_page")
        and widget.remaining_list_page is not None
    ):
        QTimer.singleShot(
            APP_INIT_DELAY, lambda: _update_remaining_list_delayed(widget)
        )


def _update_remaining_list_delayed(widget):
    try:
        if (
            hasattr(widget, "remaining_list_page")
            and widget.remaining_list_page is not None
        ):
            class_name = widget.list_combobox.currentText()
            group_filter = widget.range_combobox.currentText()
            gender_filter = widget.gender_combobox.currentText()
            group_index = widget.range_combobox.currentIndex()
            gender_index = widget.gender_combobox.currentIndex()
            half_repeat = readme_settings_async("roll_call_settings", "half_repeat")

            if hasattr(widget.remaining_list_page, "update_remaining_list"):
                widget.remaining_list_page.update_remaining_list(
                    class_name,
                    group_filter,
                    gender_filter,
                    half_repeat,
                    group_index,
                    gender_index,
                    emit_signal=False,
                    source="roll_call",
                )
            else:
                if hasattr(widget.remaining_list_page, "class_name"):
                    widget.remaining_list_page.class_name = class_name
                if hasattr(widget.remaining_list_page, "group_filter"):
                    widget.remaining_list_page.group_filter = group_filter
                if hasattr(widget.remaining_list_page, "gender_filter"):
                    widget.remaining_list_page.gender_filter = gender_filter
                if hasattr(widget.remaining_list_page, "group_index"):
                    widget.remaining_list_page.group_index = group_index
                if hasattr(widget.remaining_list_page, "gender_index"):
                    widget.remaining_list_page.gender_index = gender_index
                if hasattr(widget.remaining_list_page, "half_repeat"):
                    widget.remaining_list_page.half_repeat = half_repeat

                if hasattr(widget.remaining_list_page, "count_changed"):
                    widget.remaining_list_page.count_changed.emit(
                        widget.remaining_count
                    )
    except Exception as e:
        logger.exception(f"延迟更新剩余名单时发生错误: {e}")
