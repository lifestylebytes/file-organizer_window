from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox,
    QRadioButton, QTextEdit, QFileDialog, QMessageBox, QButtonGroup
)
from PySide6.QtCore import Qt, QEvent
from pathlib import Path

from organizer.settings import load_settings, save_settings, reset_settings
from organizer.core import organize_desktop
from organizer.undo import undo_last_operation


class FileOrganizerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileOrganizer · v1.0")
        self.resize(760, 680)

        self.settings = load_settings()
        layout = QVBoxLayout(self)



        # ===== 대상 폴더 =====
        self.target_label = QLabel(f"대상 폴더: {self.settings['target_dir']}")
        btn_change = QPushButton("변경")
        btn_change.clicked.connect(self.change_folder)

        row = QHBoxLayout()
        row.addWidget(self.target_label)
        row.addStretch()
        row.addWidget(btn_change)
        layout.addLayout(row)

        # ===== 분류 규칙 =====
        layout.addWidget(QLabel("분류 규칙 (Others는 자동 처리됩니다)"))

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Category", "Extensions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.load_rules()
        layout.addWidget(self.table)

        add_btn = QPushButton("+ 분류 추가")
        add_btn.clicked.connect(self.add_rule)
        layout.addWidget(add_btn)

        # Others 표시
        others_label = QLabel("• Others : 위 규칙에 해당하지 않는 모든 파일")
        others_label.setStyleSheet("color: gray;")
        layout.addWidget(others_label)

        # ===== 제외 확장자 =====
        layout.addWidget(QLabel("정리하지 않을 파일"))
        self.exclude_input = QLineEdit()
        self.exclude_input.setText(".psd .blend .aep")
        self.exclude_input.setStyleSheet("color: gray;")
        self.exclude_input.installEventFilter(self)
        layout.addWidget(self.exclude_input)

        # ===== 같은 이름 파일 처리 =====
        layout.addWidget(QLabel("같은 이름의 파일이 있을 때"))

        self.conflict_group = QButtonGroup(self)
        self.rename_radio = QRadioButton("자동으로 번호 붙이기")
        self.overwrite_radio = QRadioButton("기존 파일 덮어쓰기")

        self.conflict_group.addButton(self.rename_radio)
        self.conflict_group.addButton(self.overwrite_radio)

        layout.addWidget(self.rename_radio)
        layout.addWidget(self.overwrite_radio)

        # ✅ 여기 추가
        if self.settings.get("on_conflict") == "overwrite":
            self.rename_radio.setChecked(True)
        else:
            self.overwrite_radio.setChecked(True)



        # ===== 정리 방식 =====
        layout.addWidget(QLabel("정리 방식"))

        self.mode_group = QButtonGroup(self)
        self.move_radio = QRadioButton("폴더로 이동")
        self.inplace_radio = QRadioButton("현재 위치에서 분류")

        self.mode_group.addButton(self.move_radio)
        self.mode_group.addButton(self.inplace_radio)

        if self.settings.get("mode") == "inplace":
            self.move_radio.setChecked(True)
        else:
            self.inplace_radio.setChecked(True)



        layout.addWidget(self.move_radio)

        move_row = QHBoxLayout()
        move_row.addSpacing(24)
        move_row.addWidget(QLabel("정리 폴더 이름:"))
        self.archive_input = QLineEdit(self.settings["archive_folder"])
        move_row.addWidget(self.archive_input)
        layout.addLayout(move_row)

        layout.addWidget(self.inplace_radio)

        # ===== 숨김 =====
        self.hidden_check = QCheckBox("숨김 파일 제외")
        self.hidden_check.setChecked(self.settings["exclude_hidden"])
        layout.addWidget(self.hidden_check)

        # ===== 미리보기 =====
        layout.addWidget(QLabel("미리보기"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

        btn_preview = QPushButton("미리 보기")
        btn_preview.clicked.connect(self.preview_result)
        layout.addWidget(btn_preview)

        # ===== 하단 버튼 =====
        bottom = QHBoxLayout()
        bottom.addStretch()

        btn_reset = QPushButton("설정 초기화")
        btn_save = QPushButton("설정 저장")
        btn_run = QPushButton("정리 실행")
        undo_btn = QPushButton("되돌리기")

        btn_reset.clicked.connect(self.reset)
        btn_save.clicked.connect(self.save)
        btn_run.clicked.connect(self.run)
        undo_btn.clicked.connect(self.undo)

        bottom.addWidget(btn_reset)
        bottom.addWidget(btn_save)
        bottom.addWidget(btn_run)
        bottom.addWidget(undo_btn)

        layout.addLayout(bottom)

        # ===== Footer =====
        footer = QLabel("@youbuddy_day · youbuddy · 2026 · Version 1.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(footer)

    # ---------- helpers ----------

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "대상 폴더 선택")
        if folder:
            self.settings["target_dir"] = folder
            self.target_label.setText(f"대상 폴더: {folder}")

    def load_rules(self):
        for cat, exts in self.settings["rules"].items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cat))
            self.table.setItem(row, 1, QTableWidgetItem(" ".join(exts)))


    def eventFilter(self, obj, event):
        if obj == self.exclude_input and event.type() == QEvent.FocusIn:
            if "gray" in obj.styleSheet():
                obj.clear()
                obj.setStyleSheet("color: black;")
        return super().eventFilter(obj, event)



    def add_rule(self):
        self.table.insertRow(self.table.rowCount())

    def collect_rules(self):
        rules = {}
        used_exts = set()
        exclude = {e.lower() for e in self.exclude_input.text().split()}

        for r in range(self.table.rowCount()):
            cat_item = self.table.item(r, 0)
            ext_item = self.table.item(r, 1)

            cat = cat_item.text().strip() if cat_item else ""
            raw_exts = ext_item.text().split() if ext_item else []

            # category 비었는데 확장자 있으면 에러
            if not cat and raw_exts:
                raise ValueError("카테고리 이름이 비어 있는 행이 있습니다.")

            if not cat or not raw_exts:
                continue

            if cat in rules:
                raise ValueError(f"카테고리 이름 중복: {cat}")

            exts = []
            for e in raw_exts:
                e = e.lower()   # ⭐ 핵심
                if not e.startswith("."):
                    raise ValueError(f"확장자는 .으로 시작해야 합니다: {e}")

                if e in used_exts:
                    raise ValueError(f"확장자 중복: {e}")

                if e in exclude:
                    raise ValueError(f"제외 확장자와 충돌: {e}")

                used_exts.add(e)
                exts.append(e)

            rules[cat] = exts

        if not rules:
            raise ValueError("최소 한 개 이상의 분류 규칙이 필요합니다.")

        return rules

        rules = {}
        used_exts = set()
        exclude = set(self.exclude_input.text().split())

        for r in range(self.table.rowCount()):
            cat_item = self.table.item(r, 0)
            ext_item = self.table.item(r, 1)

            cat = cat_item.text().strip() if cat_item else ""
            exts = ext_item.text().split() if ext_item else []

            # ❗ category 비었는데 확장자 있으면 에러
            if not cat and exts:
                raise ValueError("카테고리 이름이 비어 있는 행이 있습니다.")

            if not cat or not exts:
                continue

            if cat in rules:
                raise ValueError(f"카테고리 이름 중복: {cat}")

            for e in exts:
                if e in used_exts:
                    raise ValueError(f"확장자 중복: {e}")
                if e in exclude:
                    raise ValueError(f"제외 확장자와 충돌: {e}")
                used_exts.add(e)

            rules[cat] = exts

        if not rules:
            raise ValueError("최소 한 개 이상의 분류 규칙이 필요합니다.")

        return rules

        rules = {}
        used_exts = set()
        exclude = set(self.exclude_input.text().split())

        for r in range(self.table.rowCount()):
            cat_item = self.table.item(r, 0)
            ext_item = self.table.item(r, 1)
            if not cat_item or not ext_item:
                continue

            cat = cat_item.text().strip()
            exts = ext_item.text().split()

            if cat in rules:
                raise ValueError("같은 카테고리 이름이 중복되었습니다.")

            for e in exts:
                if e in used_exts:
                    raise ValueError(f"확장자 중복: {e}")
                if e in exclude:
                    raise ValueError(f"제외 확장자와 충돌: {e}")
                used_exts.add(e)

            rules[cat] = exts

        return rules

    def preview_result(self):
        try:
            rules = self.collect_rules()
            lines = []
            for cat, exts in rules.items():
                for e in exts:
                    lines.append(f"{e} → {cat}/")
            lines.append("* 그 외 파일 → Others/")
            self.preview.setText("\n".join(lines))
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

    def save(self):
        if not self.conflict_group.checkedButton():
            QMessageBox.warning(self, "오류", "같은 이름 파일 처리 방식을 선택하세요.")
            return False

        if not self.mode_group.checkedButton():
            QMessageBox.warning(self, "오류", "정리 방식을 선택하세요.")
            return False

        try:
            rules = self.collect_rules()
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            return False

        self.settings.update({
            "rules": rules,
            "exclude_extensions": self.exclude_input.text().split(),
            "on_conflict": "overwrite" if self.overwrite_radio.isChecked() else "rename",
            "mode": "move" if self.move_radio.isChecked() else "inplace",
            "archive_folder": self.archive_input.text().strip() or "Archive",
            "exclude_hidden": self.hidden_check.isChecked(),
        })

        save_settings(self.settings)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
        return True

        if not self.conflict_group.checkedButton():
            QMessageBox.warning(self, "오류", "같은 이름 파일 처리 방식을 선택하세요.")
            return

        if not self.mode_group.checkedButton():
            QMessageBox.warning(self, "오류", "정리 방식을 선택하세요.")
            return

        try:
            rules = self.collect_rules()
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))
            return

        self.settings.update({
            "rules": rules,
            "exclude_extensions": self.exclude_input.text().split(),
            "on_conflict": "overwrite" if self.overwrite_radio.isChecked() else "rename",
            "mode": "move" if self.move_radio.isChecked() else "inplace",
            "archive_folder": self.archive_input.text().strip() or "Archive",
            "exclude_hidden": self.hidden_check.isChecked(),
        })

        save_settings(self.settings)
        QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")

    def run(self):
        if not self.save():
                return

        rules_flat = {
            ext: cat
            for cat, exts in self.settings["rules"].items()
            for ext in exts
        }

        organize_desktop(
            target_dir=Path(self.settings["target_dir"]),
            rules=rules_flat,
            exclude_extensions=self.settings["exclude_extensions"],
            mode=self.settings["mode"],
            conflict_mode=self.settings["on_conflict"],
            archive_folder=self.settings["archive_folder"],
            exclude_hidden=self.settings["exclude_hidden"],
        )

        QMessageBox.information(self, "완료", "파일 정리가 완료되었습니다.")

    def undo(self):
        try:
            undo_last_operation()
            QMessageBox.information(self, "완료", "마지막 정리 작업을 되돌렸습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

    def reset(self):
        self.settings = reset_settings()
        self.table.setRowCount(0)
        self.load_rules()
        self.exclude_input.setText(" ".join(self.settings["exclude_extensions"]))
        self.archive_input.setText(self.settings["archive_folder"])
        self.rename_radio.setChecked(False)
        self.overwrite_radio.setChecked(False)
        self.move_radio.setChecked(False)
        self.inplace_radio.setChecked(False)
        self.preview.clear()
        QMessageBox.information(self, "완료", "설정이 초기화되었습니다.")
