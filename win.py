import sys
import os
import re
import ctypes
import shutil
import platform
try:
    import winreg
except ImportError:
    winreg = None

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMainWindow,
    QActionGroup, QFileDialog, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QStackedWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings, QTimer, QThread, pyqtSignal, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QIcon

from qfluentwidgets import (
    LineEdit, PrimaryPushButton, PushButton, ComboBox, CheckBox,
    SubtitleLabel, CaptionLabel, BodyLabel, ProgressBar,
    setTheme, Theme, setThemeColor, isDarkTheme, RoundMenu, Action, FluentIcon,
    SpinBox, ToolTipFilter, MessageBox, SegmentedWidget, TableWidget, ToolButton, SwitchButton
)

# Optional Mutagen for Metadata
try:
    import mutagen
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

# ── Registry helpers ──────────────────────────────────────────────────────────

def _reg_dword(hive, path, name, default=None):
    if winreg is None: return default
    try:
        key = winreg.OpenKey(hive, path)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return default

def _get_system_theme() -> str:
    val = _reg_dword(
        winreg.HKEY_CURRENT_USER if winreg else None,
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        "AppsUseLightTheme", default=1
    )
    return "dark" if val == 0 else "light"

def _get_accent_color() -> str:
    val = _reg_dword(
        winreg.HKEY_CURRENT_USER if winreg else None,
        r"Software\Microsoft\Windows\DWM",
        "AccentColor", default=None
    )
    if val is None:
        return "#0078d4"
    val = val & 0xFFFFFFFF
    b = (val >> 16) & 0xFF
    g = (val >> 8) & 0xFF
    r = val & 0xFF
    return f"#{r:02X}{g:02X}{b:02X}"

# ── Çeviriler ─────────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "tr": {
        "window_title": "YNRename", "add_files": "Dosya Ekle", "add_folder": "Klasör Ekle",
        "remove_selected": "Seçilileri Sil", "clear_list": "Listeyi Temizle", "rename_btn": "Yeniden Adlandır", "undo_btn": "Geri Al",
        "col_old": "Eski İsim", "col_new": "Yeni İsim", "col_path": "Yol",
        "tab_text": "Metin", "tab_case": "Harf", "tab_additions": "Eklentiler", "tab_clean": "Temizlik", "tab_meta": "Metadata", "tab_regex": "Regex",
        "find_label": "Bul:", "replace_label": "Değiştir:", "case_sensitive": "Büyük/Küçük Duyarlı", "use_regex": "Regex Kullan",
        "meta_format": "Format:", "meta_help": "Etiketler:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nMüzik:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Hazır. {count} dosya.", "status_renaming": "Değiştiriliyor...", "status_done": "Tamamlandı! {count} dosya.",
        "menu_language": "Dil", "placeholder_find": "Bulunacak metin...", "placeholder_meta": "{artist} - {title}",
        "case_none": "Değişiklik Yok", "case_lower": "küçük harf", "case_upper": "BÜYÜK HARF", "case_title": "Başlık Düzeni", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Ayraç:", "add_text": "Metin:", "add_date": "Tarih Ekle", "add_time": "Saat Ekle", "add_num": "Numaralandır", "num_start": "Başlangıç:", "num_step": "Artış:", "num_digits": "Basamak:",
        "clean_turkish": "Türkçe Karakterleri Dönüştür", "clean_spaces": "Boşlukları Alt Çizgi Yap", "clean_os_chars": "OS Karakterlerini Temizle", "trim_start": "Baştan Kırp:", "trim_end": "Sondan Kırp:", "trim_between": "Arasından Kırp:",
        "regex_pattern": "Desen:", "regex_replace": "Değiştir:", "menu_remove": "Listeden Kaldır", "dlg_add_title": "Dosyaları Seç", "dlg_folder_title": "Klasör Seç",
        "mutagen_required": "Bu özellik için Mutagen kütüphanesi gerekli.", "pos_suffix": "Sona Ekle (Suffix)", "pos_prefix": "Başa Ekle (Prefix)",
        "status_error": "Hata: {msg}", "status_undo_done": "Geri alma başarılı! {count} dosya.",
        "menu_theme": "Tema", "theme_dark": "Koyu", "theme_light": "Açık", "theme_auto": "Otomatik (Sistem)",
        "err_title": "Hata", "err_conflict": "Çakışma var! Bazı dosyalar aynı ismi alıyor.",
        "err_no_files": "İşlem yapılacak dosya yok.", "err_undo": "Geri alınacak işlem yok.",
        "tooltip_toggle_panel": "Sağ Paneli Gizle / Göster", "status_conflict": "Çakışma var! Bazı dosyalar aynı ismi alıyor."
    },
    "en": {
        "window_title": "YNRename", "add_files": "Add Files", "add_folder": "Add Folder",
        "remove_selected": "Remove Selected", "clear_list": "Clear List", "rename_btn": "Rename", "undo_btn": "Undo",
        "col_old": "Old Name", "col_new": "New Name", "col_path": "Path",
        "tab_text": "Text", "tab_case": "Case", "tab_additions": "Additions", "tab_clean": "Clean", "tab_meta": "Metadata", "tab_regex": "Regex",
        "find_label": "Find:", "replace_label": "Replace:", "case_sensitive": "Case Sensitive", "use_regex": "Use Regex",
        "meta_format": "Format:", "meta_help": "Tags:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nMusic:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Ready. {count} files.", "status_renaming": "Renaming...", "status_done": "Done! {count} files.",
        "menu_language": "Language", "placeholder_find": "Text to find...", "placeholder_meta": "{artist} - {title}",
        "case_none": "No Change", "case_lower": "lowercase", "case_upper": "UPPERCASE", "case_title": "Title Case", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Separator:", "add_text": "Text:", "add_date": "Add Date", "add_time": "Add Time", "add_num": "Add Numbering", "num_start": "Start:", "num_step": "Step:", "num_digits": "Digits:",
        "clean_turkish": "Convert Turkish Chars", "clean_spaces": "Spaces to Underscores", "clean_os_chars": "Clean OS Chars", "trim_start": "Trim Start:", "trim_end": "Trim End:", "trim_between": "Trim Between:",
        "regex_pattern": "Pattern:", "regex_replace": "Replace:", "menu_remove": "Remove from List", "dlg_add_title": "Select Files", "dlg_folder_title": "Select Folder",
        "mutagen_required": "Mutagen library required for this feature.", "pos_suffix": "Add to End (Suffix)", "pos_prefix": "Add to Start (Prefix)",
        "status_error": "Error: {msg}", "status_undo_done": "Undo successful! {count} files.",
        "menu_theme": "Theme", "theme_dark": "Dark", "theme_light": "Light", "theme_auto": "Auto (System)",
        "err_title": "Error", "err_conflict": "Conflicting filenames!", "tooltip_toggle_panel": "Toggle Right Panel",
        "err_no_files": "No files to process.", "err_undo": "Nothing to undo.", "status_conflict": "Conflict! Filenames match."
    },
    "fr": {
        "window_title": "YNRename", "add_files": "Ajouter des fichiers", "add_folder": "Ajouter un dossier",
        "remove_selected": "Supprimer la sélection", "clear_list": "Vider la liste", "rename_btn": "Renommer", "undo_btn": "Annuler",
        "col_old": "Ancien Nom", "col_new": "Nouveau Nom", "col_path": "Chemin",
        "tab_text": "Texte", "tab_case": "Casse", "tab_additions": "Ajouts", "tab_clean": "Nettoyer", "tab_meta": "Méta", "tab_regex": "Regex",
        "find_label": "Trouver:", "replace_label": "Remplacer:", "case_sensitive": "Sensible à la casse", "use_regex": "Utiliser Regex",
        "meta_format": "Format:", "meta_help": "Étiquettes:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nMusique:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Prêt. {count} fichiers.", "status_renaming": "Renommage...", "status_done": "Terminé! {count} fichiers.",
        "menu_language": "Langue", "placeholder_find": "Texte à trouver...", "placeholder_meta": "{artist} - {title}",
        "case_none": "Pas de changement", "case_lower": "minuscule", "case_upper": "MAJUSCULE", "case_title": "Casse de titre", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Séparateur:", "add_text": "Texte:", "add_date": "Ajouter date", "add_time": "Ajouter heure", "add_num": "Numéroter", "num_start": "Début:", "num_step": "Pas:", "num_digits": "Chiffres:",
        "clean_turkish": "Convertir caract. turcs", "clean_spaces": "Espaces en underscores", "clean_os_chars": "Nettoyer caract. OS", "trim_start": "Rogner début:", "trim_end": "Rogner fin:", "trim_between": "Rogner entre:",
        "regex_pattern": "Motif:", "regex_replace": "Remplacer:", "menu_remove": "Retirer de la liste", "dlg_add_title": "Sélectionner fichiers", "dlg_folder_title": "Sélectionner dossier",
        "mutagen_required": "Mutagen requis.", "pos_suffix": "Ajouter à la fin", "pos_prefix": "Ajouter au début",
        "status_error": "Erreur: {msg}", "status_undo_done": "Annulation réussie! {count} fichiers.",
        "menu_theme": "Thème", "theme_dark": "Sombre", "theme_light": "Clair", "theme_auto": "Auto",
        "err_title": "Erreur", "err_conflict": "Noms de fichiers en conflit!", "tooltip_toggle_panel": "Basculer le panneau"
    },
    "es": {
        "window_title": "YNRename", "add_files": "Añadir archivos", "add_folder": "Añadir carpeta",
        "remove_selected": "Eliminar seleccionados", "clear_list": "Limpiar lista", "rename_btn": "Renombrar", "undo_btn": "Deshacer",
        "col_old": "Nombre Antiguo", "col_new": "Nombre Nuevo", "col_path": "Ruta",
        "tab_text": "Texto", "tab_case": "Capa", "tab_additions": "Adiciones", "tab_clean": "Limpiar", "tab_meta": "Meta", "tab_regex": "Regex",
        "find_label": "Buscar:", "replace_label": "Reemplazar:", "case_sensitive": "Distinguir mayúsculas", "use_regex": "Usar Regex",
        "meta_format": "Formato:", "meta_help": "Etiquetas:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nMúsica:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Listo. {count} archivos.", "status_renaming": "Renombrando...", "status_done": "Hecho! {count} archivos.",
        "menu_language": "Idioma", "placeholder_find": "Texto a buscar...", "placeholder_meta": "{artist} - {title}",
        "case_none": "Sin cambios", "case_lower": "minúsculas", "case_upper": "MAYÚSCULAS", "case_title": "Tipo Título", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Separador:", "add_text": "Texto:", "add_date": "Añadir fecha", "add_time": "Añadir hora", "add_num": "Numerar", "num_start": "Inicio:", "num_step": "Paso:", "num_digits": "Dígitos:",
        "clean_turkish": "Convertir caract. turcos", "clean_spaces": "Espacios a guiones", "clean_os_chars": "Limpiar caract. SO", "trim_start": "Recortar inicio:", "trim_end": "Recortar fin:", "trim_between": "Recortar entre:",
        "regex_pattern": "Patrón:", "regex_replace": "Reemplazar:", "menu_remove": "Quitar de la lista", "dlg_add_title": "Seleccionar archivos", "dlg_folder_title": "Seleccionar carpeta",
        "mutagen_required": "Mutagen requerido.", "pos_suffix": "Añadir al final", "pos_prefix": "Añadir al inicio",
        "status_error": "Error: {msg}", "status_undo_done": "Deshacer éxito! {count} archivos.",
        "menu_theme": "Tema", "theme_dark": "Oscuro", "theme_light": "Claro", "theme_auto": "Auto",
        "err_title": "Error", "err_conflict": "¡Nombres de archivo en conflicto!", "tooltip_toggle_panel": "Alternar panel"
    },
    "it": {
        "window_title": "YNRename", "add_files": "Aggiungi file", "add_folder": "Aggiungi cartella",
        "remove_selected": "Rimuovi selezionati", "clear_list": "Svuota lista", "rename_btn": "Rinomina", "undo_btn": "Annulla",
        "col_old": "Vecchio Nome", "col_new": "Nuovo Nome", "col_path": "Percorso",
        "tab_text": "Testo", "tab_case": "Casi", "tab_additions": "Aggiunte", "tab_clean": "Pulisci", "tab_meta": "Meta", "tab_regex": "Regex",
        "find_label": "Trova:", "replace_label": "Sostituisci:", "case_sensitive": "Maiuscole/minuscole", "use_regex": "Usa Regex",
        "meta_format": "Formato:", "meta_help": "Tag:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nMusica:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Pronto. {count} file.", "status_renaming": "Rinomina...", "status_done": "Fatto! {count} file.",
        "menu_language": "Lingua", "placeholder_find": "Testo da trovare...", "placeholder_meta": "{artist} - {title}",
        "case_none": "Nessuna modifica", "case_lower": "minuscolo", "case_upper": "MAIUSCOLO", "case_title": "Iniziali Maiuscole", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Separatore:", "add_text": "Testo:", "add_date": "Aggiungi data", "add_time": "Aggiungi ora", "add_num": "Numerazione", "num_start": "Inizio:", "num_step": "Passo:", "num_digits": "Cifre:",
        "clean_turkish": "Converti caratt. turchi", "clean_spaces": "Spazi in underscore", "clean_os_chars": "Pulisci caratt. OS", "trim_start": "Taglia inizio:", "trim_end": "Taglia fine:", "trim_between": "Taglia tra:",
        "regex_pattern": "Modello:", "regex_replace": "Sostituisci:", "menu_remove": "Rimuovi dalla lista", "dlg_add_title": "Seleziona file", "dlg_folder_title": "Seleziona cartella",
        "mutagen_required": "Mutagen richiesto.", "pos_suffix": "Aggiungi alla fine", "pos_prefix": "Aggiungi all'inizio",
        "status_error": "Errore: {msg}", "status_undo_done": "Annullamento riuscito! {count} file.",
        "menu_theme": "Tema", "theme_dark": "Scuro", "theme_light": "Chiaro", "theme_auto": "Auto",
        "err_title": "Errore", "err_conflict": "Nomi di file in conflitto!", "tooltip_toggle_panel": "Alterna pannello"
    },
    "ru": {
        "window_title": "YNRename", "add_files": "Добавить файлы", "add_folder": "Добавить папку",
        "remove_selected": "Удалить выбранные", "clear_list": "Очистить список", "rename_btn": "Переименовать", "undo_btn": "Отменить",
        "col_old": "Старое Имя", "col_new": "Новое Имя", "col_path": "Путь",
        "tab_text": "Текст", "tab_case": "Регистр", "tab_additions": "Дополнения", "tab_clean": "Очистка", "tab_meta": "Мета", "tab_regex": "Regex",
        "find_label": "Найти:", "replace_label": "Заменить:", "case_sensitive": "Учитывать регистр", "use_regex": "Исп. Regex",
        "meta_format": "Формат:", "meta_help": "Теги:\n{oldname}, {name}, {folder}, {size}, {date}, {time}, {ext}\n{cdate}, {mdate}\nМузыка:\n{artist}, {title}, {album}, {year}, {genre}, {track}",
        "status_ready": "Готово. {count} файлов.", "status_renaming": "Переименование...", "status_done": "Готово! {count} файлов.",
        "menu_language": "Язык", "placeholder_find": "Текст для поиска...", "placeholder_meta": "{artist} - {title}",
        "case_none": "Без изменений", "case_lower": "строчные", "case_upper": "ПРОПИСНЫЕ", "case_title": "Как в заголовке", "case_camel": "camelCase", "case_snake": "snake_case", "case_kebab": "kebab-case",
        "add_sep": "Разделитель:", "add_text": "Текст:", "add_date": "Добавить дату", "add_time": "Добавить время", "add_num": "Нумерация", "num_start": "Старт:", "num_step": "Шаг:", "num_digits": "Разряды:",
        "clean_turkish": "Конвертировать турецкие буквы", "clean_spaces": "Пробелы в подчеркивания", "clean_os_chars": "Очистить символы ОС", "trim_start": "Обрезать начало:", "trim_end": "Обрезать конец:", "trim_between": "Обрезать между:",
        "regex_pattern": "Шаблон:", "regex_replace": "Замена:", "menu_remove": "Удалить из списка", "dlg_add_title": "Выбрать файлы", "dlg_folder_title": "Выбрать папку",
        "mutagen_required": "Библиотека Mutagen обязательна.", "pos_suffix": "Добавить в конец", "pos_prefix": "Добавить в начало",
        "status_error": "Ошибка: {msg}", "status_undo_done": "Отмена успешна! {count} файлов.",
        "menu_theme": "Тема", "theme_dark": "Темная", "theme_light": "Светлая", "theme_auto": "Авто",
        "err_title": "Ошибка", "err_conflict": "Конфликт имен файлов!", "tooltip_toggle_panel": "Скрыть/Показать панель"
    }
}

# ── Logic ─────────────────────────────────────────────────────────────────────

class RenameLogic:
    @staticmethod
    def apply_find_replace(name, find, repl, case_sensitive, use_regex):
        if not find: return name
        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return re.sub(find, repl, name, flags=flags)
            except: return name
        else:
            if case_sensitive: return name.replace(find, repl)
            else:
                pattern = re.compile(re.escape(find), re.IGNORECASE)
                return pattern.sub(repl, name)

    @staticmethod
    def apply_case(name, mode):
        base, ext = os.path.splitext(name)
        if mode == "case_lower": base = base.lower()
        elif mode == "case_upper": base = base.upper()
        elif mode == "case_title": base = base.title()
        elif mode == "case_camel":
            words = [w for w in re.split(r'[^a-zA-Z0-9]', base) if w]
            if words: base = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        elif mode == "case_snake":
            base = '_'.join(w.lower() for w in re.split(r'[^a-zA-Z0-9]', base) if w)
        elif mode == "case_kebab":
            base = '-'.join(w.lower() for w in re.split(r'[^a-zA-Z0-9]', base) if w)
        return base + ext

    @staticmethod
    def apply_additions(name, is_suffix, sep, text, do_date, do_time, do_num, num_idx, start, step, digits):
        base, ext = os.path.splitext(name)
        parts = []
        if text: parts.append(text)
        from datetime import datetime
        if do_date: parts.append(datetime.now().strftime("%Y-%m-%d"))
        if do_time: parts.append(datetime.now().strftime("%H-%M-%S"))
        if do_num: parts.append(str(start + (num_idx * step)).zfill(digits))
        if not parts: return name
        addon = sep.join(parts)
        if is_suffix: res = f"{base}{sep}{addon}" if base else addon
        else: res = f"{addon}{sep}{base}" if base else addon
        return res + ext

    @staticmethod
    def apply_clean(name, turkish, spaces, os_chars, trim_start=0, trim_end=0, trim_b1="", trim_b2=""):
        base, ext = os.path.splitext(name)
        if turkish:
            tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
            base = base.translate(tr_map)
        if spaces: base = base.replace(" ", "_")
        if os_chars:
            invalid = r'[<>:"/\\|?*]' if platform.system() == "Windows" else r'[/]'
            base = re.sub(invalid, "", base)
        if trim_start > 0: base = base[trim_start:]
        if trim_end > 0 and len(base) > trim_end: base = base[:-trim_end]
        if trim_b1 and trim_b2:
            base = re.sub(re.escape(trim_b1) + r'.*?' + re.escape(trim_b2), "", base)
        return base + ext

    @staticmethod
    def apply_metadata(path, name, format_str, original_name):
        if not format_str: return name
        try:
            base, ext_with_dot = os.path.splitext(name)
            ext = ext_with_dot.replace(".", "")
            orig_base, _ = os.path.splitext(original_name)
            folder_name = os.path.basename(os.path.dirname(path)) if path else ""
            size_bytes = os.path.getsize(path) if path and os.path.exists(path) else 0
            if size_bytes > 1048576: size_str = f"{size_bytes/1048576:.1f}MB"
            elif size_bytes > 1024: size_str = f"{size_bytes/1024:.1f}KB"
            else: size_str = f"{size_bytes}B"
            from datetime import datetime
            dt_now = datetime.now()
            cdate = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d") if path and os.path.exists(path) else ""
            mdate = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d") if path and os.path.exists(path) else ""
            tag_map = {
                "{oldname}": orig_base, "{old_name}": orig_base, "{name}": base, "{prefix}": base,
                "{folder}": folder_name, "{ext}": ext, "{size}": size_str, "{s}": size_str,
                "{date}": mdate, "{d}": mdate, "{cdate}": cdate, "{mdate}": mdate, "{md}": mdate,
                "{time}": dt_now.strftime("%H-%M-%S"), "{t}": dt_now.strftime("%H-%M-%S")
            }
            res_str = format_str
            for tag, val in tag_map.items():
                res_str = re.compile(re.escape(tag), re.IGNORECASE).sub(val, res_str)
            if HAS_MUTAGEN:
                try:
                    f = mutagen.File(path, easy=True) or mutagen.File(path)
                    if f:
                        m_tags = {'artist': '', 'title': '', 'album': '', 'year': '', 'genre': '', 'track': ''}
                        def _get(ks):
                            for k in ks:
                                if k in f:
                                    v = f[k]
                                    return str(v[0]) if isinstance(v, list) and v else str(v)
                            return ''
                        m_tags['artist'] = _get(['artist', 'TPE1', 'ARTIST'])
                        m_tags['title'] = _get(['title', 'TIT2', 'TITLE'])
                        m_tags['album'] = _get(['album', 'TALB', 'ALBUM'])
                        d_val = _get(['date', 'TDRC', 'TYER', 'DATE'])
                        if d_val and len(d_val) >= 4: m_tags['year'] = d_val[:4]
                        m_tags['genre'] = _get(['genre', 'TCON', 'GENRE'])
                        tr_val = _get(['tracknumber', 'TRCK', 'TRACKNUMBER'])
                        if tr_val: m_tags['track'] = tr_val.split('/')[0].zfill(2)
                        for k, v in m_tags.items():
                            res_str = re.compile(re.escape(f"{{{k}}}"), re.IGNORECASE).sub(v or "", res_str)
                except: pass
            res_str = re.sub(r'^[\s\-_]+|[\s\-_]+$', '', res_str).replace(' -  - ', ' - ').replace('__', '_').replace('--', '-')
            return (re.sub(r'\s+', ' ', res_str).strip() + ext_with_dot) if res_str else name
        except: return name

    @staticmethod
    def apply_regex(name, pattern, replacement):
        if not pattern: return name
        try: return re.sub(pattern, replacement, name)
        except: return name

# ── Threads ───────────────────────────────────────────────────────────────────

class RenameThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, rename_map):
        super().__init__()
        self.rename_map = rename_map

    def run(self):
        results = []
        total = len(self.rename_map)
        for i, (old_path, new_name) in enumerate(self.rename_map.items()):
            dir_name = os.path.dirname(old_path)
            new_path = os.path.join(dir_name, new_name)
            
            if old_path != new_path:
                try:
                    os.rename(old_path, new_path)
                    results.append((old_path, new_path))
                except Exception as e:
                    self.error.emit(str(e))
                    continue
                    
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit(results)

class UndoThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, history_map):
        super().__init__()
        self.history_map = history_map

    def run(self):
        results = []
        total = len(self.history_map)
        for i, (old_path, new_path) in enumerate(self.history_map):
            if old_path != new_path and os.path.exists(new_path):
                try:
                    os.rename(new_path, old_path)
                    results.append((new_path, old_path))
                except Exception as e:
                    self.error.emit(str(e))
                    continue
            self.progress.emit(int((i + 1) / total * 100))
        self.finished.emit(results)


# ── UI Elements ───────────────────────────────────────────────────────────────

class YNRename(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("ynrename.ico"))
        self.settings = QSettings("YNRename", "YNRenameFluent")
        self._current_lang = str(self.settings.value("language", "tr"))
        self._current_theme = str(self.settings.value("theme", "auto"))
        
        if self._current_theme == "dark":
            setTheme(Theme.DARK)
        elif self._current_theme == "light":
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK if _get_system_theme() == "dark" else Theme.LIGHT)

        self.files = []
        self.history = []
        
        setThemeColor(_get_accent_color())
        self.menuBar().setNativeMenuBar(False)

        central = QWidget()
        self.setCentralWidget(central)
        self.setAcceptDrops(True)
        self.resize(1150, 700)
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._do_preview)
        
        self._panel_natural_width = 320
        self.panel_animation = QVariantAnimation(self)
        self.panel_animation.setDuration(300)
        self.panel_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.panel_animation.valueChanged.connect(self._on_anim_step)
        self.panel_animation.finished.connect(self._on_anim_finished)

        self._build_menubar()
        self._build_ui(central)
        self._retranslate_ui()
        self._apply_theme(self._current_theme)

    def _t(self, key, **kw):
        text = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["en"]).get(key, key)
        return text.format(**kw) if kw else text

    # ── Theme & Menubar ───────────────────────────────────────────────────────

    def _apply_theme(self, theme_str):
        self._current_theme = theme_str
        if theme_str == "dark":
            setTheme(Theme.DARK)
        elif theme_str == "light":
            setTheme(Theme.LIGHT)
        else:
            sys_t = _get_system_theme()
            setTheme(Theme.DARK if sys_t == "dark" else Theme.LIGHT)

        is_dark = isDarkTheme()
        bg_color = "#1a1a1a" if is_dark else "#f3f3f3"

        if is_dark:
            mb_style = """
                QMenuBar { background-color: transparent; color: white; padding: 0px; }
                QMenuBar::item { background: transparent; padding: 6px 12px; border-radius: 4px; }
                QMenuBar::item:selected { background: rgba(255, 255, 255, 0.1); }
                QMenuBar::item:pressed { background: rgba(255, 255, 255, 0.15); }
            """
            widget_style = """
                BodyLabel { color: #ffffff; }
                CaptionLabel { color: #ffffff; }
                CheckBox { color: #ffffff; }
            """
        else:
            mb_style = """
                QMenuBar { background-color: transparent; color: black; padding: 0px; }
                QMenuBar::item { background: transparent; padding: 6px 12px; border-radius: 4px; }
                QMenuBar::item:selected { background: rgba(0, 0, 0, 0.05); }
                QMenuBar::item:pressed { background: rgba(0, 0, 0, 0.1); }
            """
            widget_style = """
                BodyLabel { color: #000000; }
                CaptionLabel { color: #666666; }
                CheckBox { color: #000000; }
            """

        self.setStyleSheet(f"YNRename {{ background-color: {bg_color}; }}\n{mb_style}\n{widget_style}")
        self._set_title_bar_dark(is_dark)

    def _set_title_bar_dark(self, dark):
        try:
            hwnd = int(self.winId())
            value = ctypes.c_int(1 if dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except: pass

    def _build_menubar(self):
        mb = self.menuBar()
        mb.setMinimumHeight(32)
        mb.clear()

        # Theme
        self.theme_menu = RoundMenu(self._t("menu_theme"), self)
        self.theme_menu.setIcon(FluentIcon.PALETTE)
        tg = QActionGroup(self)
        tg.setExclusive(True)
        for k, lk, icn in [("auto", "theme_auto", FluentIcon.SYNC), ("light", "theme_light", FluentIcon.BRIGHTNESS), ("dark", "theme_dark", FluentIcon.QUIET_HOURS)]:
            is_sel = (self._current_theme == k)
            act = Action(FluentIcon.ACCEPT if is_sel else icn, self._t(lk), self, checkable=True)
            act.setChecked(is_sel)
            act.triggered.connect(lambda checked, val=k: self._on_theme(val))
            tg.addAction(act)
            self.theme_menu.addAction(act)
        mb.addMenu(self.theme_menu)

        # Language
        self.lang_menu = RoundMenu(self._t("menu_language"), self)
        self.lang_menu.setIcon(FluentIcon.LANGUAGE)
        lg = QActionGroup(self)
        lg.setExclusive(True)
        for k, label in [("tr", "Türkçe"), ("en", "English"), ("fr", "Français"), ("es", "Español"), ("it", "Italiano"), ("ru", "Русский")]:
            is_sel = (self._current_lang == k)
            act = Action(FluentIcon.ACCEPT if is_sel else FluentIcon.GLOBE, label, self, checkable=True)
            act.setChecked(is_sel)
            act.triggered.connect(lambda checked, val=k: self._on_language(val))
            lg.addAction(act)
            self.lang_menu.addAction(act)
        mb.addMenu(self.lang_menu)

    def _on_theme(self, theme):
        self.settings.setValue("theme", theme)
        self._apply_theme(theme)
        self._build_menubar()

    def _on_language(self, lang):
        self._current_lang = lang
        self.settings.setValue("language", lang)
        self._build_menubar()
        self._retranslate_ui()

    # ── UI Building ───────────────────────────────────────────────────────────

    def _build_ui(self, central):
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        self.btn_add_files = PushButton(FluentIcon.DOCUMENT, "")
        self.btn_add_folder = PushButton(FluentIcon.FOLDER_ADD, "")
        self.btn_remove_sel = PushButton(FluentIcon.REMOVE, "")
        self.btn_clear = PushButton(FluentIcon.DELETE, "")
        self.btn_toggle_panel = ToolButton(FluentIcon.RIGHT_ARROW)
        
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_remove_sel.clicked.connect(self._remove_checked)
        self.btn_clear.clicked.connect(self._clear_list)
        self.btn_toggle_panel.clicked.connect(self._toggle_right_panel)

        top_bar.addWidget(self.btn_add_files)
        top_bar.addWidget(self.btn_add_folder)
        top_bar.addWidget(self.btn_remove_sel)
        top_bar.addWidget(self.btn_clear)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_toggle_panel)
        layout.addLayout(top_bar)

        # Main Split
        main_split = QHBoxLayout()
        
        # Left: Table
        self.table = TableWidget(self)
        self.table.setColumnCount(3)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.setBorderRadius(8)
        self.table.setBorderVisible(True)
        self.table.setDragDropMode(QAbstractItemView.InternalMove)
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.model().rowsMoved.connect(self._on_rows_moved)
        
        # Right: Tabs
        self.right_panel = QWidget()
        self.right_panel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.right_panel.setMinimumWidth(320)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        
        right_layout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        right_layout.addWidget(self.stackedWidget, 1)
        
        self._build_tab_text()
        self._build_tab_case()
        self._build_tab_additions()
        self._build_tab_clean()
        self._build_tab_meta()
        self._build_tab_regex()

        main_split.addWidget(self.table, 1)
        main_split.addWidget(self.right_panel, 0)
        layout.addLayout(main_split)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.lbl_status = CaptionLabel("")
        self.progress = ProgressBar()
        self.progress.setValue(0)
        self.progress.hide()
        
        self.btn_undo = PushButton("")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self._undo_rename)
        
        self.btn_rename = PrimaryPushButton(FluentIcon.EDIT, "")
        self.btn_rename.clicked.connect(self._start_rename)
        
        bottom_bar.addWidget(self.lbl_status)
        bottom_bar.addWidget(self.progress)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.btn_undo)
        bottom_bar.addWidget(self.btn_rename)
        
        layout.addLayout(bottom_bar)

    def _build_tab_text(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.lbl_find = BodyLabel()
        l.addWidget(self.lbl_find)
        self.in_find = LineEdit()
        l.addWidget(self.in_find)
        self.lbl_replace = BodyLabel()
        l.addWidget(self.lbl_replace)
        self.in_replace = LineEdit()
        l.addWidget(self.in_replace)
        self.chk_case = CheckBox()
        l.addWidget(self.chk_case)
        self.chk_regex = CheckBox()
        l.addWidget(self.chk_regex)
        
        for widget in [self.in_find, self.in_replace, self.chk_case, self.chk_regex]:
            if hasattr(widget, 'textChanged'): widget.textChanged.connect(self._queue_preview)
            if hasattr(widget, 'stateChanged'): widget.stateChanged.connect(self._queue_preview)
            
        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _build_tab_case(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(5, 10, 5, 5)
        self.combo_case = ComboBox()
        self.combo_case.currentIndexChanged.connect(self._queue_preview)
        l.addWidget(self.combo_case)
        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _build_tab_additions(self):
        w = QWidget()
        l = QVBoxLayout(w)
        
        # Switch Position
        h_pos = QHBoxLayout()
        self.lbl_pos = BodyLabel()
        self.switch_pos = SwitchButton()
        self.switch_pos.setOnText("")
        self.switch_pos.setOffText("")
        self.switch_pos.checkedChanged.connect(self._queue_preview)
        h_pos.addWidget(self.switch_pos)
        h_pos.addWidget(self.lbl_pos)
        h_pos.addStretch()
        l.addLayout(h_pos)
        
        # Separator & Custom Text
        h_text = QHBoxLayout()
        self.lbl_add_sep = BodyLabel()
        self.in_add_sep = LineEdit()
        self.in_add_sep.setText("_")
        self.in_add_sep.setFixedWidth(50)
        self.lbl_add_text = BodyLabel()
        self.in_add_text = LineEdit()
        h_text.addWidget(self.lbl_add_sep)
        h_text.addWidget(self.in_add_sep)
        h_text.addWidget(self.lbl_add_text)
        h_text.addWidget(self.in_add_text)
        l.addLayout(h_text)
        
        # Date / Time
        h_dt = QHBoxLayout()
        self.chk_add_date = CheckBox()
        self.chk_add_time = CheckBox()
        h_dt.addWidget(self.chk_add_date)
        h_dt.addWidget(self.chk_add_time)
        l.addLayout(h_dt)
        
        # Numbering
        self.chk_add_num = CheckBox()
        l.addWidget(self.chk_add_num)
        
        h_num1 = QHBoxLayout()
        self.lbl_num_start = BodyLabel()
        self.spin_start = SpinBox(); self.spin_start.setRange(0, 9999)
        self.lbl_num_step = BodyLabel()
        self.spin_step = SpinBox(); self.spin_step.setRange(1, 100)
        h_num1.addWidget(self.lbl_num_start); h_num1.addWidget(self.spin_start)
        h_num1.addWidget(self.lbl_num_step); h_num1.addWidget(self.spin_step)
        l.addLayout(h_num1)
        
        h_num2 = QHBoxLayout()
        self.lbl_num_digits = BodyLabel()
        self.spin_digits = SpinBox(); self.spin_digits.setRange(1, 10)
        h_num2.addWidget(self.lbl_num_digits); h_num2.addWidget(self.spin_digits)
        h_num2.addStretch()
        l.addLayout(h_num2)

        for widget in [self.in_add_text, self.in_add_sep]: widget.textChanged.connect(self._queue_preview)
        for widget in [self.spin_start, self.spin_step, self.spin_digits]: widget.valueChanged.connect(self._queue_preview)
        for chk in [self.chk_add_date, self.chk_add_time, self.chk_add_num]: chk.stateChanged.connect(self._queue_preview)

        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _build_tab_clean(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.chk_clean_tr = CheckBox()
        self.chk_clean_sp = CheckBox()
        self.chk_clean_os = CheckBox()
        for chk in [self.chk_clean_tr, self.chk_clean_sp, self.chk_clean_os]:
            chk.stateChanged.connect(self._queue_preview)
            l.addWidget(chk)
            
        l.addSpacing(10)
        
        h_trim1 = QHBoxLayout()
        self.lbl_trim_start = BodyLabel()
        self.spin_trim_start = SpinBox(); self.spin_trim_start.setRange(0, 100)
        self.lbl_trim_end = BodyLabel()
        self.spin_trim_end = SpinBox(); self.spin_trim_end.setRange(0, 100)
        h_trim1.addWidget(self.lbl_trim_start); h_trim1.addWidget(self.spin_trim_start)
        h_trim1.addWidget(self.lbl_trim_end); h_trim1.addWidget(self.spin_trim_end)
        l.addLayout(h_trim1)
        
        h_trim2 = QHBoxLayout()
        self.lbl_trim_between = BodyLabel()
        self.in_trim_b1 = LineEdit(); self.in_trim_b1.setFixedWidth(40)
        self.in_trim_b2 = LineEdit(); self.in_trim_b2.setFixedWidth(40)
        h_trim2.addWidget(self.lbl_trim_between)
        h_trim2.addWidget(self.in_trim_b1)
        h_trim2.addWidget(self.in_trim_b2)
        h_trim2.addStretch()
        l.addLayout(h_trim2)
        
        for w_ in [self.spin_trim_start, self.spin_trim_end]: w_.valueChanged.connect(self._queue_preview)
        for w_ in [self.in_trim_b1, self.in_trim_b2]: w_.textChanged.connect(self._queue_preview)
            
        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _build_tab_meta(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(5, 10, 5, 5)
        self.lbl_meta_help = BodyLabel()
        self.lbl_meta_format = BodyLabel()
        self.in_meta_format = LineEdit()
        self.in_meta_format.setPlaceholderText("{artist} - {title}")
        self.in_meta_format.textChanged.connect(self._queue_preview)
        
        l.addWidget(self.lbl_meta_help)
        l.addSpacing(10)
        l.addWidget(self.lbl_meta_format)
        l.addWidget(self.in_meta_format)
        
        if not HAS_MUTAGEN:
            self.in_meta_format.setToolTip(self._t("mutagen_required"))
            
        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _build_tab_regex(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(5, 10, 5, 5)
        self.lbl_regex_pat = BodyLabel()
        self.in_regex_pat = LineEdit()
        self.lbl_regex_rep = BodyLabel()
        self.in_regex_rep = LineEdit()
        
        for widget in [self.in_regex_pat, self.in_regex_rep]:
            widget.textChanged.connect(self._queue_preview)
            
        l.addWidget(self.lbl_regex_pat)
        l.addWidget(self.in_regex_pat)
        l.addWidget(self.lbl_regex_rep)
        l.addWidget(self.in_regex_rep)
        l.addStretch()
        self.stackedWidget.addWidget(w)

    def _retranslate_ui(self):
        self.setWindowTitle(self._t("window_title"))
        self.btn_add_files.setText(self._t("add_files"))
        self.btn_add_folder.setText(self._t("add_folder"))
        self.btn_remove_sel.setText(self._t("remove_selected"))
        self.btn_clear.setText(self._t("clear_list"))
        self.btn_rename.setText(self._t("rename_btn"))
        self.btn_undo.setText(self._t("undo_btn"))
        
        self.table.setHorizontalHeaderLabels([self._t("col_old"), self._t("col_new"), self._t("col_path")])
        
        # Re-populate Pivot
        current_idx = max(0, self.stackedWidget.currentIndex())
        self.pivot.clear()
        self.pivot.addItem(routeKey='tab_text', text=self._t("tab_text"), onClick=lambda: self.stackedWidget.setCurrentIndex(0))
        self.pivot.addItem(routeKey='tab_case', text=self._t("tab_case"), onClick=lambda: self.stackedWidget.setCurrentIndex(1))
        self.pivot.addItem(routeKey='tab_additions', text=self._t("tab_additions"), onClick=lambda: self.stackedWidget.setCurrentIndex(2))
        self.pivot.addItem(routeKey='tab_clean', text=self._t("tab_clean"), onClick=lambda: self.stackedWidget.setCurrentIndex(3))
        self.pivot.addItem(routeKey='tab_meta', text=self._t("tab_meta"), onClick=lambda: self.stackedWidget.setCurrentIndex(4))
        self.pivot.addItem(routeKey='tab_regex', text=self._t("tab_regex"), onClick=lambda: self.stackedWidget.setCurrentIndex(5))
        
        route_keys = ['tab_text', 'tab_case', 'tab_additions', 'tab_clean', 'tab_meta', 'tab_regex']
        self.pivot.setCurrentItem(route_keys[current_idx])
        
        # Labels
        self.lbl_find.setText(self._t("find_label"))
        self.lbl_replace.setText(self._t("replace_label"))
        self.chk_case.setText(self._t("case_sensitive"))
        self.chk_regex.setText(self._t("use_regex"))
        self.in_find.setPlaceholderText(self._t("placeholder_find"))
        self.in_replace.setPlaceholderText(self._t("replace_label").replace(":", "..."))
        
        idx = self.combo_case.currentIndex()
        self.combo_case.clear()
        self.combo_case.addItems([self._t(k) for k in ["case_none", "case_lower", "case_upper", "case_title", "case_camel", "case_snake", "case_kebab"]])
        self.combo_case.setCurrentIndex(max(0, idx))
        
        self.lbl_pos.setText(self._t("pos_suffix") if self.switch_pos.isChecked() else self._t("pos_prefix"))
        self.lbl_add_sep.setText(self._t("add_sep"))
        self.lbl_add_text.setText(self._t("add_text"))
        self.chk_add_date.setText(self._t("add_date"))
        self.chk_add_time.setText(self._t("add_time"))
        self.chk_add_num.setText(self._t("add_num"))
        self.lbl_num_start.setText(self._t("num_start"))
        self.lbl_num_step.setText(self._t("num_step"))
        self.lbl_num_digits.setText(self._t("num_digits"))
        
        self.chk_clean_tr.setText(self._t("clean_turkish"))
        self.chk_clean_sp.setText(self._t("clean_spaces"))
        self.chk_clean_os.setText(self._t("clean_os_chars"))
        self.lbl_trim_start.setText(self._t("trim_start"))
        self.lbl_trim_end.setText(self._t("trim_end"))
        self.lbl_trim_between.setText(self._t("trim_between"))
        
        self.lbl_meta_help.setText(self._t("meta_help"))
        self.lbl_meta_format.setText(self._t("meta_format"))
        self.in_meta_format.setPlaceholderText(self._t("placeholder_meta"))
        
        self.lbl_regex_pat.setText(self._t("regex_pattern"))
        self.lbl_regex_rep.setText(self._t("regex_replace"))
        
        self.lbl_status.setText(self._t("status_ready", count=len(self.files)))
        self.btn_toggle_panel.setToolTip(self._t("tooltip_toggle_panel"))
        self._build_menubar()

    # ── Logic & Events ────────────────────────────────────────────────────────

    def _on_anim_step(self, value):
        self.right_panel.setFixedWidth(value)

    def _on_anim_finished(self):
        if self.right_panel.width() > 0:
            self.right_panel.setMinimumWidth(320)
            self.right_panel.setMaximumWidth(16777215)

    def _toggle_right_panel(self):
        if self.right_panel.width() > 0:
            self._panel_natural_width = self.right_panel.width()
            self.panel_animation.setStartValue(self._panel_natural_width)
            self.panel_animation.setEndValue(0)
            self.btn_toggle_panel.setIcon(FluentIcon.LEFT_ARROW)
        else:
            self.panel_animation.setStartValue(0)
            self.panel_animation.setEndValue(max(self._panel_natural_width, 320))
            self.btn_toggle_panel.setIcon(FluentIcon.RIGHT_ARROW)
        self.panel_animation.start()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self._process_dropped_paths(paths)

    def _process_dropped_paths(self, paths):
        for p in paths:
            if os.path.isfile(p):
                self._add_file_to_list(p)
            elif os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        self._add_file_to_list(os.path.join(root, f))
        self._queue_preview()

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self._t("dlg_add_title"))
        self._process_dropped_paths(paths)

    def _add_folder(self):
        path = QFileDialog.getExistingDirectory(self, self._t("dlg_folder_title"))
        if path:
            self._process_dropped_paths([path])

    def _add_file_to_list(self, path):
        if any(f['path'] == path for f in self.files): return
        name = os.path.basename(path)
        self.files.append({'path': path, 'old_name': name, 'new_name': name})

    def _remove_checked(self):
        self.files = [f for f in self.files if not f.get('checked', False)]
        self._queue_preview()

    def _remove_highlighted(self):
        rows = [item.row() for item in self.table.selectedItems()]
        if hasattr(self, '_clicked_row') and self._clicked_row not in rows and self._clicked_row is not None:
            rows.append(self._clicked_row)
        unique_rows = sorted(list(set(rows)), reverse=True)
        for r in unique_rows:
            if r < len(self.files): del self.files[r]
        self._queue_preview()
        self._clicked_row = None

    def _clear_list(self):
        self.files.clear()
        self.table.setRowCount(0)
        self.lbl_status.setText(self._t("status_ready", count=0))

    def _on_rows_moved(self, parent, start, end, destination, row):
        moved = self.files[start:end+1]
        del self.files[start:end+1]
        insert_idx = row if row < start else row - (end - start + 1)
        for i, item in enumerate(moved):
            self.files.insert(insert_idx + i, item)
        self._queue_preview()

    def _queue_preview(self):
        self.preview_timer.start(150)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        self._clicked_row = item.row()
        menu = RoundMenu(parent=self)
        act_remove = Action(FluentIcon.DELETE, self._t("menu_remove"), self)
        act_remove.triggered.connect(self._remove_highlighted)
        menu.addAction(act_remove)
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def _on_table_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            if row < len(self.files):
                self.files[row]['checked'] = (item.checkState() == Qt.Checked)

    def _do_preview(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.files))
        
        find = self.in_find.text()
        repl = self.in_replace.text()
        case_sen = self.chk_case.isChecked()
        use_regex = self.chk_regex.isChecked()
        
        case_idx = self.combo_case.currentIndex()
        case_map = [None, "case_lower", "case_upper", "case_title", "case_camel", "case_snake", "case_kebab"]
        case_mode = case_map[case_idx] if case_idx > 0 else None
        
        is_suffix = self.switch_pos.isChecked()
        add_sep = self.in_add_sep.text()
        add_text = self.in_add_text.text()
        do_date = self.chk_add_date.isChecked()
        do_time = self.chk_add_time.isChecked()
        do_num = self.chk_add_num.isChecked()
        start = self.spin_start.value()
        step = self.spin_step.value()
        digits = self.spin_digits.value()
        
        cln_tr = self.chk_clean_tr.isChecked()
        cln_sp = self.chk_clean_sp.isChecked()
        cln_os = self.chk_clean_os.isChecked()
        t_start = self.spin_trim_start.value()
        t_end = self.spin_trim_end.value()
        t_b1 = self.in_trim_b1.text()
        t_b2 = self.in_trim_b2.text()
        
        m_format = self.in_meta_format.text()
        rx_pat = self.in_regex_pat.text()
        rx_rep = self.in_regex_rep.text()

        new_names_set = set()

        for i, f in enumerate(self.files):
            name = f['old_name']
            name = RenameLogic.apply_find_replace(name, find, repl, case_sen, use_regex)
            if case_mode: name = RenameLogic.apply_case(name, case_mode)
            name = RenameLogic.apply_additions(name, is_suffix, add_sep, add_text, do_date, do_time, do_num, i, start, step, digits)
            name = RenameLogic.apply_clean(name, cln_tr, cln_sp, cln_os, t_start, t_end, t_b1, t_b2)
            if m_format: name = RenameLogic.apply_metadata(f['path'], name, m_format, f['old_name'])
            name = RenameLogic.apply_regex(name, rx_pat, rx_rep)
            
            f['new_name'] = name
            item_old = QTableWidgetItem(f['old_name'])
            item_old.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item_old.setCheckState(Qt.Checked if f.get('checked', False) else Qt.Unchecked)
            self.table.setItem(i, 0, item_old)
            
            item_new = QTableWidgetItem(name)
            self.table.setItem(i, 1, item_new)
            self.table.setItem(i, 2, QTableWidgetItem(f['path']))
            
            original_base, original_ext = os.path.splitext(name)
            target_dir = os.path.dirname(f['path'])
            target_path = os.path.join(target_dir, name)
            key = target_path.lower() if platform.system() == "Windows" else target_path
            
            counter = 1
            while key in new_names_set or (os.path.exists(target_path) and key != f['path'].lower()):
                name = f"{original_base}_{counter}{original_ext}"
                target_path = os.path.join(target_dir, name)
                key = target_path.lower() if platform.system() == "Windows" else target_path
                counter += 1
                item_new.setForeground(QColor(255, 60, 60))
                
            new_names_set.add(key)
            
        self.lbl_status.setText(self._t("status_ready", count=len(self.files)))
        self.table.blockSignals(False)

    def _start_rename(self):
        if not self.files: return
        rename_map = {f['path']: f['new_name'] for f in self.files if f['old_name'] != f['new_name']}
        if not rename_map: return
        self.btn_rename.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        self.lbl_status.setText(self._t("status_renaming"))
        self.thread = RenameThread(rename_map)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self._on_rename_finished)
        self.thread.error.connect(lambda e: self.lbl_status.setText(self._t("status_error", msg=e)))
        self.thread.start()

    def _on_rename_finished(self, results):
        self.btn_rename.setEnabled(True)
        self.progress.hide()
        self.history = results
        self.btn_undo.setEnabled(len(self.history) > 0)
        self._clear_list()
        self.lbl_status.setText(self._t("status_done", count=len(results)))

    def _undo_rename(self):
        if not self.history: return
        self.btn_undo.setEnabled(False)
        self.progress.show()
        self.progress.setValue(0)
        self.thread = UndoThread(self.history)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self._on_undo_finished)
        self.thread.error.connect(lambda e: self.lbl_status.setText(self._t("status_error", msg=e)))
        self.thread.start()

    def _on_undo_finished(self, results):
        self.btn_undo.setEnabled(False)
        self.progress.hide()
        self.history.clear()
        self.lbl_status.setText(self._t("status_undo_done", count=len(results)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = "ynrename.ico"
    app.setWindowIcon(QIcon(icon_path))
    window = YNRename()
    window.show()
    sys.exit(app.exec_())
