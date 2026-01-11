from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem,
    QCheckBox, QRadioButton, QTextEdit,
    QFileDialog
)
from organizer.settings import load_settings, save_settings
from organizer.platform import get_desktop_path


class SettingsUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("파일 정리 설정")

        self.settings = load_settings()

        layout = QVBoxLayout(self)

        # 대상 폴더
        self.target_label = QLabel(
            f"대상 폴더: {self.settings.get('target_dir') or get_desktop_path()}"
        )
        change_btn = QPushButton("변경")
        change_btn.clicked.connect(self.change_folder)

        row = QHBoxLayout()
        row.addWidget(self.target_label)
        row.addWidget(change_btn)
        layout.addLayout(row)

        # 분류 규칙 테이블
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category", "Extensions"])
        self.load_rules()
        layout.addWidget(self.table)

        add_btn = QPushButton("+ 분류 추가")
        add_btn.clicked.connect(self.add_rule)
        layout.addWidget(add_btn)

        # 제외 확장자
        self.exclude_input = QLineEdit(
            " ".join(self.settings["exclude_extensions"])
        )
        layout.addWidget(QLabel("정리하지 않을 확장자"))
        layout.addWidget(self.exclude_input)

        # 충돌 처리
        layout.addWidget(QLabel("같은 이름의 파일이 있을 때"))
        self.rename_radio = QRadioButton("자동으로 번호 붙이기 (권장)")
        self.overwrite_radio = QRadioButton("기존 파일 덮어쓰기")

        if self.settings["on_conflict"] == "rename":
            self.rename_radio.setChecked(True)
        else:
            self.overwrite_radio.setChecked(True)

        layout.addWidget(self.rename_radio)
        layout.addWidget(self.overwrite_radio)

        # 숨김 파일
        self.hidden_check = QCheckBox("숨김 파일 제외 (.DS_Store 등)")
        self.hidden_check.setChecked(self.settings["exclude_hidden"])
        layout.addWidget(self.hidden_check)

        # 미리보기
        self.preview = QTextEdit()
        self.preview.setPlaceholderText("정리 결과 미리보기")
        layout.addWidget(self.preview)

        # 저장 버튼
        save_btn = QPushButton("설정 저장")
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "대상 폴더 선택")
        if folder:
            self.settings["target_dir"] = folder
            self.target_label.setText(f"대상 폴더: {folder}")

    def load_rules(self):
        for category, exts in self.settings["rules"].items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(category))
            self.table.setItem(row, 1, QTableWidgetItem(" ".join(exts)))

    def add_rule(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

    def save(self):
        rules = {}
        for row in range(self.table.rowCount()):
            cat = self.table.item(row, 0)
            ext = self.table.item(row, 1)
            if cat and ext:
                rules[cat.text()] = ext.text().split()

        self.settings.update({
            "rules": rules,
            "exclude_extensions": self.exclude_input.text().split(),
            "on_conflict": "rename" if self.rename_radio.isChecked() else "overwrite",
            "exclude_hidden": self.hidden_check.isChecked()
        })

        save_settings(self.settings)
        self.close()
