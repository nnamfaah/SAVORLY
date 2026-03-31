import sys
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QFont

from main_login import LoginWindow
from Database_sor import init_database, run_migrations, ensure_meals_unique, fix_db_on_startup
import stylesheet as ss 

def main():
    try:
        print("🚀 Starting Savorly App...")
        try:
            init_database()
            print("✅ Database initialized")
        except Exception as e:
            print("❌ DB init error:", e)
            traceback.print_exc()

        try:
            run_migrations()
            print("✅ Migrations done")
        except Exception as e:
            print("⚠️ Migration skipped:", e)

        try: 
            fix_db_on_startup()
            print("✅ Fix_database done")

        except Exception as e:
            print("⚠️ Fix_database skipped", e)

        try:
            ensure_meals_unique()
            print("✅ ensure_meal done")
        except Exception as e:
            print("⚠️ Ensure_meal skipped", e)

        app = QApplication(sys.argv)
        app.setFont(QFont("Inria Serif", 10))

        app.setStyleSheet(ss.app_global)

        window = LoginWindow()
        window.show()

        print("✅ UI Launched")
        sys.exit(app.exec())

    except Exception as e:
        print("💥 FATAL ERROR:", e)
        traceback.print_exc()
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Application crashed:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()