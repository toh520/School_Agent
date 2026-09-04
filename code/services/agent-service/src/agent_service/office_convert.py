"""Isolated, timeout-bounded Microsoft Office conversion helper."""

import sys
from pathlib import Path


def convert(source: Path, target: Path) -> None:
    """Convert one legacy Office file to PDF without enabling macros or editing it."""

    try:
        import pythoncom
        import win32com.client
    except ImportError as exception:
        raise RuntimeError("解析旧版 DOC/PPT 需要 LibreOffice 或 Microsoft Office") from exception
    pythoncom.CoInitialize()
    application = document = None
    try:
        if source.suffix.lower() == ".doc":
            application = win32com.client.DispatchEx("Word.Application")
            application.Visible = False
            application.DisplayAlerts = 0
            application.AutomationSecurity = 3
            document = application.Documents.Open(
                str(source),
                ConfirmConversions=False,
                ReadOnly=True,
                AddToRecentFiles=False,
                Visible=False,
                OpenAndRepair=True,
            )
            document.SaveAs(str(target), FileFormat=17)
        else:
            application = win32com.client.DispatchEx("PowerPoint.Application")
            application.AutomationSecurity = 3
            document = application.Presentations.Open(
                str(source), ReadOnly=True, Untitled=False, WithWindow=False
            )
            document.SaveAs(str(target), 32)
    finally:
        if document is not None:
            document.Close()
        if application is not None:
            application.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: office_convert.py SOURCE TARGET")
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
