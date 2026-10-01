"""Record actual Qt motion with synthetic states, isolated data, no microphone or model."""

import argparse
import os
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import av
    import numpy as np
    from PyQt6.QtCore import QMimeData, QPoint, QPointF, QRect, Qt, QUrl
    from PyQt6.QtGui import (
        QColor,
        QDragEnterEvent,
        QDropEvent,
        QFont,
        QFontDatabase,
        QImage,
        QPainter,
    )
    from PyQt6.QtWidgets import QApplication

    with tempfile.TemporaryDirectory(prefix="nexus-motion-preview-") as temporary:
        os.environ["NEXUS_DATA_DIR"] = temporary
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        os.environ["NEXUS_TTS_ENABLED"] = "0"
        from backend.user_settings import settings_store
        from frontend.app import SpotlightApp

        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
            if (fonts / name).exists():
                QFontDatabase.addApplicationFont(str(fonts / name))
        preferences = settings_store.load()
        preferences.setup_complete = True
        preferences.language = "tr"
        preferences.reduced_motion = False
        preferences.providers[0].selected_model = "Örnek yerel model"
        settings_store.save(preferences)
        window = SpotlightApp()
        window.show()
        # Keep the synthetic playback pose stable; real wake state refresh is not
        # part of this isolated recording and would overwrite it every 250 ms.
        window.wake.timer.stop()
        document = Path(temporary) / "ornek-proje.txt"
        document.write_text("Proje: Nexus. Amaç: yerel ve kolay kullanılabilir bir asistan.", encoding="utf-8")
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(document))])
        stage = -1
        title = ""
        snapshots = {4: "listening", 6: "thinking", 8: "speaking", 9: "drop", 11: "attachment", 15: "success", 18: "error"}
        captured = set()
        fps, seconds, width, height = 24, 21, 960, 760
        with av.open(str(args.output), "w") as container:
            stream = container.add_stream("libx264", rate=fps)
            stream.width, stream.height, stream.pix_fmt = width, height, "yuv420p"
            stream.options = {"crf": "22", "preset": "veryfast"}
            began = time.perf_counter()
            for index in range(fps * seconds):
                moment = index / fps
                current = next((i for i, start in reversed(list(enumerate([0, 1.1, 2, 3, 5, 7, 8.8, 10, 12, 14, 16, 17.5, 19.5]))) if moment >= start), 0)
                if current != stage:
                    stage = current
                    if stage == 0:
                        title = "Asistanın gelişi"
                    elif stage == 1:
                        title = "Kısa bakış ve göz kırpma"
                        window.dock_avatar.blink_animation.start()
                    elif stage == 2:
                        title = "Düğmelerin tepkisi"
                        window.dock_tools[1]._hover(1)
                        window.dock_tools[1]._ripple()
                    elif stage == 3:
                        title = "Dinleme halkaları"
                        window.dock_tools[1]._hover(0)
                        window._recording_ready = True
                        window._refresh_visual_activity()
                    elif stage == 4:
                        title = "Düşünürken bakış ve dönen noktalar"
                        window._recording_ready = False
                        window._response_complete = False
                        window._refresh_visual_activity()
                        window.update_status("Kurgu sorunun yanıtı hazırlanıyor…")
                    elif stage == 5:
                        title = "Seslendirme sırasında konuşma hareketi"
                        window.dock_avatar.set_mode("speaking")
                        window.dock_title.setText("Nexus konuşuyor")
                        window.dock_status.setText("Kurgu seslendirme durumu")
                    elif stage == 6:
                        title = "Belgeyi bırakacağın alan"
                        window._response_complete = True
                        window._refresh_visual_activity()
                        event = QDragEnterEvent(QPoint(200, 150), Qt.DropAction.CopyAction, mime,
                                               Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                        window.dragEnterEvent(event)
                    elif stage == 7:
                        title = "Belge ekleme ve sohbetin açılması"
                        with patch("frontend.app.request_json", return_value={"id": "synthetic-preview"}):
                            window.dropEvent(QDropEvent(QPointF(200, 150), Qt.DropAction.CopyAction, mime,
                                                        Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
                    elif stage == 8:
                        title = "Yanıt sırasında hareketli durum göstergesi"
                        window._show_output()
                        window.input_line.clear()
                        window.question_label.setText("Örnek projeyi özetle.")
                        window._response_complete = False
                        window._refresh_visual_activity()
                        window.append_response("## Daha kolay bir yerel asistan\n\nNexus; sohbeti, belgelerini ve sesli iletişimi tek bir yerde toplar.")
                    elif stage == 9:
                        title = "Tamamlandığında kısa onay tepkisi"
                        window.append_response("\n\n- Yerel modelini seç.\n- Belgeni ekle.\n- Sorunu yaz veya konuş.")
                        window.complete_response()
                    elif stage == 10:
                        title = "Panel'e yumuşak dönüş"
                        window.set_shell_mode("dock")
                    elif stage == 11:
                        title = "Hata için farklı bir ifade"
                        window.display_error("Bu, hata ifadesini gösteren kurgusal bir örnektir.")
                    elif stage == 12:
                        title = "Hareketi azalt: durum bilgisi korunur"
                        window.apply_motion_preference(True)
                        window.set_shell_mode("dock")
                delay = began + index / fps - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                app.processEvents()
                canvas = QImage(width, height, QImage.Format.Format_RGB888)
                canvas.fill(QColor("#0b1011"))
                painter = QPainter(canvas)
                painter.setPen(QColor("#e5f5ea"))
                painter.setFont(QFont("Segoe UI", 17, QFont.Weight.DemiBold))
                painter.drawText(QRect(20, 12, width - 40, 44), Qt.AlignmentFlag.AlignCenter, title)
                pixmap = window.grab()
                painter.drawPixmap((width - pixmap.width()) // 2, 67, pixmap)
                painter.setPen(QColor("#97a99e"))
                painter.setFont(QFont("Segoe UI", 10))
                painter.drawText(QRect(10, height - 42, width - 20, 28), Qt.AlignmentFlag.AlignCenter,
                                 "Gerçek arayüz · kurgu durumlar · model ve mikrofon çalıştırılmadı")
                painter.end()
                second = int(moment)
                if second in snapshots and second not in captured:
                    canvas.save(str(args.output.with_name(f"motion-{snapshots[second]}.png")))
                    captured.add(second)
                pixels = np.frombuffer(canvas.constBits().asstring(canvas.sizeInBytes()), dtype=np.uint8)
                pixels = pixels.reshape(height, canvas.bytesPerLine())[:, :width * 3].reshape(height, width, 3)
                frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
                frame.pts, frame.time_base = index, Fraction(1, fps)
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        window.close()
        app.processEvents()
    print(args.output.resolve())


if __name__ == "__main__":
    main()
