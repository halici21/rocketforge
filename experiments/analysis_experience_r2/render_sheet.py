import pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView, QQuickWindow  # noqa: F401
import main as app_main

app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
view = QQuickView()
view.engine().addImportPath(str(app_main.UI_DIR))
view.setSource(QUrl.fromLocalFile(str(ROOT / "experiments/analysis_experience_r2/icon_sheet.qml")))
for e in view.errors():
    print("ERR", e.toString())
view.resize(980, 320)
view.show()
for _ in range(40):
    app.processEvents(); time.sleep(0.02)
out = ROOT / "acceptance/analysis_experience_r2_implementation/navigation/icon_contact_sheet.png"
view.grabWindow().save(str(out))
print("sheet at", out)
