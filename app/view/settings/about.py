# ==================================================
# 导入库
# ==================================================

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtNetwork import *
from qfluentwidgets import *
from qfluentwidgets import FluentIcon as FIF

from app.tools.variable import *
from app.tools.path_utils import *
from app.tools.personalised import *
from app.tools.settings_default import *
from app.tools.settings_access import *
from app.Language.obtain_language import *

from app.page_building.another_window import create_contributor_window


# ==================================================
# 关于主容器类
# ==================================================
class about(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 创建垂直布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        # 添加横幅组件
        self.banner_widget = about_banner(self)
        self.vBoxLayout.addWidget(self.banner_widget)

        # 添加关于信息组件
        self.about_info_widget = about_info(self)
        self.vBoxLayout.addWidget(self.about_info_widget)


# ==================================================
# 横幅组件类
# ==================================================
class about_banner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        banner_path = get_data_path("assets/icon", "secrandom-banner.png")
        self.banner_image = ImageLabel(f"{banner_path}")
        self.banner_image.scaledToHeight(300)
        self.banner_image.setBorderRadius(12, 12, 12, 12)
        self.banner_image.setScaledContents(True)

        # 添加横幅图片到布局
        self.vBoxLayout = QHBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 使图片居中
        self.vBoxLayout.addWidget(self.banner_image, 0, Qt.AlignmentFlag.AlignCenter)


# ==================================================
# 关于信息组件类
# ==================================================
class about_info(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(get_content_name_async("about", "title"))
        self.setBorderRadius(8)

        # 打开GitHub按钮
        self.about_github_Button = HyperlinkButton(
            FIF.GITHUB, GITHUB_WEB, get_content_name_async("about", "github")
        )
        github_widget = self._create_button_with_icon(
            self.about_github_Button, "assets/icon", "sectl-icon.png"
        )

        # 打开bilibili按钮
        self.about_bilibili_Button = HyperlinkButton(
            FIF.GLOBE, BILIBILI_WEB, get_content_name_async("about", "bilibili")
        )
        bilibili_widget = self._create_button_with_icon(
            self.about_bilibili_Button, "assets/contribution", "contributor1.png"
        )

        # 打开网站按钮
        self.about_website_Button = HyperlinkButton(
            FIF.GLOBE, WEBSITE, get_content_name_async("about", "website")
        )
        website_widget = self._create_button_with_icon(
            self.about_website_Button, "assets/icon", "secrandom-icon-paper.png"
        )

        # 查看当前软件版本号
        version_text = f"{SPECIAL_VERSION} | {CODENAME} ({SYSTEM}-{ARCH})"
        self.about_version_label = BodyLabel(version_text)

        # 查看当前软件版权所属
        # 根据发布年份和当前年份是否相同，决定显示格式
        if INITIAL_AUTHORING_YEAR <= CURRENT_YEAR:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR} {COPYRIGHT_HOLDER}"
        else:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR}-{CURRENT_YEAR} {COPYRIGHT_HOLDER}"

        self.about_author_label = BodyLabel(copyright_text)
        copyright_widget = self._create_label_with_icon(
            self.about_author_label, "assets/icon", "sectl-icon.png"
        )

        # 创建贡献人员按钮
        self.contributor_button = PushButton(
            get_content_name_async("about", "contributor")
        )
        self.contributor_button.setIcon(
            get_theme_icon("ic_fluent_document_person_20_filled")
        )
        self.contributor_button.clicked.connect(self.show_contributors)

        # 创建捐赠支持按钮
        self.donation_button = PushButton(get_content_name_async("about", "donation"))
        self.donation_button.setIcon(
            get_theme_icon("ic_fluent_document_person_20_filled")
        )
        self.donation_button.clicked.connect(self.open_donation_url)

        self.addGroup(
            get_theme_icon("ic_fluent_branch_fork_link_20_filled"),
            get_content_name_async("about", "bilibili"),
            get_content_description_async("about", "bilibili"),
            bilibili_widget,
        )
        self.addGroup(
            FIF.GITHUB,
            get_content_name_async("about", "github"),
            get_content_description_async("about", "github"),
            github_widget,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_document_person_20_filled"),
            get_content_name_async("about", "contributor"),
            get_content_description_async("about", "contributor"),
            self.contributor_button,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_document_person_20_filled"),
            get_content_name_async("about", "donation"),
            get_content_description_async("about", "donation"),
            self.donation_button,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_class_20_filled"),
            get_content_name_async("about", "copyright"),
            get_content_description_async("about", "copyright"),
            copyright_widget,
        )
        self.addGroup(
            FIF.GLOBE,
            get_content_name_async("about", "website"),
            get_content_description_async("about", "website"),
            website_widget,
        )
        self.addGroup(
            get_theme_icon("ic_fluent_info_20_filled"),
            get_content_name_async("about", "version"),
            get_content_description_async("about", "version"),
            self.about_version_label,
        )

    def show_contributors(self):
        """显示贡献人员"""
        create_contributor_window()

    def open_donation_url(self):
        """打开捐赠链接"""
        QDesktopServices.openUrl(QUrl(DONATION_URL))

    def _create_button_with_icon(self, button, icon_dir, icon_name):
        """创建带图标的按钮容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(button)

        icon_path = get_data_path(icon_dir, icon_name)
        icon_label = ImageLabel(f"{icon_path}")
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget

    def _create_label_with_icon(self, label, icon_dir, icon_name):
        """创建带图标的标签容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(label)

        icon_path = get_data_path(icon_dir, icon_name)
        icon_label = ImageLabel(f"{icon_path}")
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget
