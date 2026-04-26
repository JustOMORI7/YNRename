import sys
import os
import re
import shutil
import platform

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMainWindow,
    QActionGroup, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QLineEdit, QCheckBox, QComboBox,
    QLabel, QSpinBox, QTabWidget, QProgressBar, QMessageBox, QAction
)
from PyQt5.QtCore import Qt, QSettings, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QColor

# Optional Mutagen for Metadata
try:
    import mutagen
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

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
        "mutagen_required": "Bu özellik için Mutagen kütüphanesi gerekli.", "pos_suffix": "Sona Ekle (Suffix)",
        "status_error": "Hata: {msg}", "status_undo_done": "Geri alma başarılı! {count} dosya."
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
        "mutagen_required": "Mutagen library required for this feature.", "pos_suffix": "Add as Suffix",
        "status_error": "Error: {msg}", "status_undo_done": "Undo successful! {count} files."
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
        "mutagen_required": "Bibliothèque Mutagen requise.", "pos_suffix": "Ajouter en suffixe",
        "status_error": "Erreur: {msg}", "status_undo_done": "Annulation réussie! {count} fichiers."
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
        "mutagen_required": "Biblioteca Mutagen requerida.", "pos_suffix": "Añadir como sufijo",
        "status_error": "Error: {msg}", "status_undo_done": "Deshacer éxito! {count} archivos."
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
        "mutagen_required": "Libreria Mutagen richiesta.", "pos_suffix": "L'aggiunta è un suffisso",
        "status_error": "Errore: {msg}", "status_undo_done": "Annullamento riuscito! {count} file."
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
        "mutagen_required": "Библиотека Mutagen обязательна.", "pos_suffix": "Добавить как суффикс",
        "status_error": "Ошибка: {msg}", "status_undo_done": "Отмена успешна! {count} файлов."
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
            except:
                return name
        else:
            if case_sensitive:
                return name.replace(find, repl)
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
            words = re.split(r'[^a-zA-Z0-9]', base)
            words = [w for w in words if w]
            if words:
                base = words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        elif mode == "case_snake":
            words = re.split(r'[^a-zA-Z0-9]', base)
            base = '_'.join(w.lower() for w in words if w)
        elif mode == "case_kebab":
            words = re.split(r'[^a-zA-Z0-9]', base)
            base = '-'.join(w.lower() for w in words if w)
        return base + ext

    @staticmethod
    def apply_additions(name, is_suffix, sep, text, do_date, do_time, do_num, num_idx, start, step, digits):
        base, ext = os.path.splitext(name)
        parts = []
        if text: parts.append(text)
        if do_date:
            from datetime import datetime
            parts.append(datetime.now().strftime("%Y-%m-%d"))
        if do_time:
            from datetime import datetime
            parts.append(datetime.now().strftime("%H-%M-%S"))
        if do_num:
            num = start + (num_idx * step)
            parts.append(str(num).zfill(digits))
            
        if not parts: return name
        
        addon = sep.join(parts)
        
        res = base
        if addon:
            if is_suffix:
                res = f"{base}{sep}{addon}" if base else addon
            else:
                res = f"{addon}{sep}{base}" if base else addon
                
        return res + ext

    @staticmethod
    def apply_clean(name, turkish, spaces, os_chars, trim_start=0, trim_end=0, trim_b1="", trim_b2=""):
        base, ext = os.path.splitext(name)
        if turkish:
            tr_map = str.maketrans("ÄŸÄžÄ±Ä°Ã¶Ã–Ã¼ÃœÅŸÅžÃ§Ã‡", "gGiIoOuUsScC")
            base = base.translate(tr_map)
        if spaces:
            base = base.replace(" ", "_")
        if os_chars:
            invalid = r'[<>:"/\\|?*]' if platform.system() == "Windows" else r'[/]'
            base = re.sub(invalid, "", base)
            
        if trim_start > 0:
            base = base[trim_start:]
        if trim_end > 0 and len(base) > trim_end:
            base = base[:-trim_end]
        if trim_b1 and trim_b2:
            pat = re.escape(trim_b1) + r'.*?' + re.escape(trim_b2)
            base = re.sub(pat, "", base)
            
        return base + ext

    @staticmethod
    def apply_metadata(path, name, format_str, original_name):
        if not format_str: return name
        try:
            # 1. Prepare Data
            base, ext_with_dot = os.path.splitext(name)
            ext = ext_with_dot.replace(".", "")
            orig_base, _ = os.path.splitext(original_name)
            folder_name = os.path.basename(os.path.dirname(path)) if path else ""
            
            size_bytes = os.path.getsize(path) if path and os.path.exists(path) else 0
            if size_bytes > 1024*1024: size_str = f"{size_bytes/(1024*1024):.1f}MB"
            elif size_bytes > 1024: size_str = f"{size_bytes/1024:.1f}KB"
            else: size_str = f"{size_bytes}B"
            
            from datetime import datetime
            dt_now = datetime.now()
            cdate = ""
            mdate = ""
            if path and os.path.exists(path):
                cdate = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y-%m-%d")
                mdate = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")

            # 2. Case-Insensitive Tag Mapping
            tag_map = {
                "{oldname}": orig_base, "{old_name}": orig_base,
                "{name}": base, "{prefix}": base,
                "{folder}": folder_name, "{ext}": ext,
                "{size}": size_str, "{s}": size_str,
                "{date}": mdate, "{d}": mdate,
                "{cdate}": cdate, "{mdate}": mdate, "{md}": mdate,
                "{time}": dt_now.strftime("%H-%M-%S"), "{t}": dt_now.strftime("%H-%M-%S")
            }

            # 3. Apply System Tags
            res_str = format_str
            for tag, val in tag_map.items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(tag), re.IGNORECASE)
                res_str = pattern.sub(val, res_str)

            # 4. Mutagen Tags (If applicable)
            if HAS_MUTAGEN and "{" in res_str and "}" in res_str:
                try:
                    try: f = mutagen.File(path, easy=True)
                    except: f = mutagen.File(path)
                    if f:
                        m_tags = {'artist': '', 'title': '', 'album': '', 'year': '', 'genre': '', 'track': ''}
                        def _get(keys):
                            for k in keys:
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
                            pat = re.compile(re.escape(f"{{{k}}}"), re.IGNORECASE)
                            res_str = pat.sub(v if v else "", res_str)
                except: pass

            # 5. Cleanup
            res_str = re.sub(r'^[\s\-_]+', '', res_str)
            res_str = re.sub(r'[\s\-_]+$', '', res_str)
            res_str = res_str.replace(' -  - ', ' - ').replace('__', '_').replace('--', '-')
            res_str = re.sub(r'\s+', ' ', res_str).strip()
            
            return (res_str + ext_with_dot) if res_str else (base + ext_with_dot)
        except Exception:
            return name

    @staticmethod
    def apply_regex(name, pattern, replacement):
        if not pattern: return name
        try:
            return re.sub(pattern, replacement, name)
        except:
            return name

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
        self.settings = QSettings("YNRename", "YNRenameMain")
        self._current_lang = str(self.settings.value("language", "tr"))
        
        self.files = []
        self.history = []
        
        central = QWidget()
        self.setCentralWidget(central)
        self.setAcceptDrops(True)
        self.resize(1000, 600)
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._do_preview)
        
        self._build_menubar()
        self._build_ui(central)
        self._retranslate_ui()

    def _t(self, key, **kw):
        text = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["en"]).get(key, key)
        return text.format(**kw) if kw else text

    # ── Menubar ───────────────────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()
        mb.clear()

        self._lang_menu = mb.addMenu(self._t("menu_language"))
        lg = QActionGroup(self)
        lg.setExclusive(True)
        for k, label in [("tr", "Türkçe"), ("en", "English"), ("fr", "Français"), ("es", "Español"), ("it", "Italiano"), ("ru", "Русский")]:
            is_sel = (self._current_lang == k)
            act = QAction(label, self, checkable=True)
            act.setChecked(is_sel)
            act.triggered.connect(lambda checked, val=k: self._on_language(val))
            lg.addAction(act)
            self._lang_menu.addAction(act)

    def _on_language(self, lang):
        self._current_lang = lang
        self.settings.setValue("language", lang)
        self._build_menubar()
        self._retranslate_ui()

    # ── UI Building ───────────────────────────────────────────────────────────

    def _build_ui(self, central):
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        self.btn_add_files = QPushButton()
        self.btn_add_folder = QPushButton()
        self.btn_remove_sel = QPushButton()
        self.btn_clear = QPushButton()
        
        self.btn_add_files.clicked.connect(self._add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_remove_sel.clicked.connect(self._remove_checked)
        self.btn_clear.clicked.connect(self._clear_list)

        top_bar.addWidget(self.btn_add_files)
        top_bar.addWidget(self.btn_add_folder)
        top_bar.addWidget(self.btn_remove_sel)
        top_bar.addWidget(self.btn_clear)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Main Split
        main_split = QHBoxLayout()
        
        # Left: Table
        self.table = QTableWidget(0, 3)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setDragDropMode(QAbstractItemView.InternalMove)
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.model().rowsMoved.connect(self._on_rows_moved)
        
        # Right: Tabs
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(350)
        
        self._build_tab_text()
        self._build_tab_case()
        self._build_tab_additions()
        self._build_tab_clean()
        self._build_tab_meta()
        self._build_tab_regex()

        main_split.addWidget(self.table, 1)
        main_split.addWidget(self.tabs, 0)
        layout.addLayout(main_split)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.lbl_status = QLabel("")
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.hide()
        
        self.btn_undo = QPushButton()
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self._undo_rename)
        
        self.btn_rename = QPushButton()
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
        self.lbl_find = QLabel()
        self.in_find = QLineEdit()
        self.lbl_replace = QLabel()
        self.in_replace = QLineEdit()
        self.chk_case = QCheckBox()
        self.chk_regex = QCheckBox()
        
        for widget in [self.in_find, self.in_replace, self.chk_case, self.chk_regex]:
            if hasattr(widget, 'textChanged'): widget.textChanged.connect(self._queue_preview)
            if hasattr(widget, 'stateChanged'): widget.stateChanged.connect(self._queue_preview)
            
        l.addWidget(self.lbl_find)
        l.addWidget(self.in_find)
        l.addWidget(self.lbl_replace)
        l.addWidget(self.in_replace)
        l.addWidget(self.chk_case)
        l.addWidget(self.chk_regex)
        l.addStretch()
        self.tabs.addTab(w, "")

    def _build_tab_case(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.combo_case = QComboBox()
        self.combo_case.currentIndexChanged.connect(self._queue_preview)
        l.addWidget(self.combo_case)
        l.addStretch()
        self.tabs.addTab(w, "")

    def _build_tab_additions(self):
        w = QWidget()
        l = QVBoxLayout(w)
        
        # Switch Position
        self.chk_pos_suffix = QCheckBox()
        self.chk_pos_suffix.stateChanged.connect(self._queue_preview)
        l.addWidget(self.chk_pos_suffix)
        
        # Separator & Custom Text
        h_text = QHBoxLayout()
        self.lbl_add_sep = QLabel()
        self.in_add_sep = QLineEdit()
        self.in_add_sep.setText("_")
        self.in_add_sep.setFixedWidth(50)
        self.lbl_add_text = QLabel()
        self.in_add_text = QLineEdit()
        h_text.addWidget(self.lbl_add_sep)
        h_text.addWidget(self.in_add_sep)
        h_text.addWidget(self.lbl_add_text)
        h_text.addWidget(self.in_add_text)
        l.addLayout(h_text)
        
        # Date / Time
        h_dt = QHBoxLayout()
        self.chk_add_date = QCheckBox()
        self.chk_add_time = QCheckBox()
        h_dt.addWidget(self.chk_add_date)
        h_dt.addWidget(self.chk_add_time)
        l.addLayout(h_dt)
        
        # Numbering
        self.chk_add_num = QCheckBox()
        l.addWidget(self.chk_add_num)
        
        h_num1 = QHBoxLayout()
        self.lbl_num_start = QLabel(); self.spin_start = QSpinBox(); self.spin_start.setRange(0, 9999)
        self.lbl_num_step = QLabel(); self.spin_step = QSpinBox(); self.spin_step.setRange(1, 100)
        h_num1.addWidget(self.lbl_num_start); h_num1.addWidget(self.spin_start)
        h_num1.addWidget(self.lbl_num_step); h_num1.addWidget(self.spin_step)
        l.addLayout(h_num1)
        
        h_num2 = QHBoxLayout()
        self.lbl_num_digits = QLabel(); self.spin_digits = QSpinBox(); self.spin_digits.setRange(1, 10)
        h_num2.addWidget(self.lbl_num_digits); h_num2.addWidget(self.spin_digits)
        h_num2.addStretch()
        l.addLayout(h_num2)

        for widget in [self.in_add_text, self.in_add_sep]: widget.textChanged.connect(self._queue_preview)
        for widget in [self.spin_start, self.spin_step, self.spin_digits]: widget.valueChanged.connect(self._queue_preview)
        for chk in [self.chk_add_date, self.chk_add_time, self.chk_add_num]: chk.stateChanged.connect(self._queue_preview)

        l.addStretch()
        self.tabs.addTab(w, "")

    def _build_tab_clean(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.chk_clean_tr = QCheckBox()
        self.chk_clean_sp = QCheckBox()
        self.chk_clean_os = QCheckBox()
        
        for chk in [self.chk_clean_tr, self.chk_clean_sp, self.chk_clean_os]:
            chk.stateChanged.connect(self._queue_preview)
            l.addWidget(chk)
            
        l.addSpacing(10)
        
        h_trim1 = QHBoxLayout()
        self.lbl_trim_start = QLabel()
        self.spin_trim_start = QSpinBox(); self.spin_trim_start.setRange(0, 100)
        self.lbl_trim_end = QLabel()
        self.spin_trim_end = QSpinBox(); self.spin_trim_end.setRange(0, 100)
        h_trim1.addWidget(self.lbl_trim_start); h_trim1.addWidget(self.spin_trim_start)
        h_trim1.addWidget(self.lbl_trim_end); h_trim1.addWidget(self.spin_trim_end)
        l.addLayout(h_trim1)
        
        h_trim2 = QHBoxLayout()
        self.lbl_trim_between = QLabel()
        self.in_trim_b1 = QLineEdit(); self.in_trim_b1.setFixedWidth(40)
        self.in_trim_b2 = QLineEdit(); self.in_trim_b2.setFixedWidth(40)
        h_trim2.addWidget(self.lbl_trim_between)
        h_trim2.addWidget(self.in_trim_b1)
        h_trim2.addWidget(self.in_trim_b2)
        h_trim2.addStretch()
        l.addLayout(h_trim2)
        
        for w_ in [self.spin_trim_start, self.spin_trim_end]: w_.valueChanged.connect(self._queue_preview)
        for w_ in [self.in_trim_b1, self.in_trim_b2]: w_.textChanged.connect(self._queue_preview)
            
        l.addStretch()
        self.tabs.addTab(w, "")

    def _build_tab_meta(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.lbl_meta_help = QLabel()
        self.lbl_meta_format = QLabel()
        self.in_meta_format = QLineEdit()
        self.in_meta_format.setPlaceholderText("{artist} - {title}")
        
        self.in_meta_format.textChanged.connect(self._queue_preview)
        
        l.addWidget(self.lbl_meta_help)
        l.addSpacing(10)
        l.addWidget(self.lbl_meta_format)
        l.addWidget(self.in_meta_format)
        
        if not HAS_MUTAGEN:
            self.in_meta_format.setToolTip(self._t("mutagen_required"))
            
        l.addStretch()
        self.tabs.addTab(w, "")

    def _build_tab_regex(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.lbl_regex_pat = QLabel()
        self.in_regex_pat = QLineEdit()
        self.lbl_regex_rep = QLabel()
        self.in_regex_rep = QLineEdit()
        
        for widget in [self.in_regex_pat, self.in_regex_rep]:
            widget.textChanged.connect(self._queue_preview)
            
        l.addWidget(self.lbl_regex_pat)
        l.addWidget(self.in_regex_pat)
        l.addWidget(self.lbl_regex_rep)
        l.addWidget(self.in_regex_rep)
        l.addStretch()
        self.tabs.addTab(w, "")

    def _retranslate_ui(self):
        self.setWindowTitle(self._t("window_title"))
        self.btn_add_files.setText(self._t("add_files"))
        self.btn_add_folder.setText(self._t("add_folder"))
        self.btn_remove_sel.setText(self._t("remove_selected"))
        self.btn_clear.setText(self._t("clear_list"))
        self.btn_rename.setText(self._t("rename_btn"))
        self.btn_undo.setText(self._t("undo_btn"))
        
        self.table.setHorizontalHeaderLabels([self._t("col_old"), self._t("col_new"), self._t("col_path")])
        
        # Tabs
        self.tabs.setTabText(0, self._t("tab_text"))
        self.tabs.setTabText(1, self._t("tab_case"))
        self.tabs.setTabText(2, self._t("tab_additions"))
        self.tabs.setTabText(3, self._t("tab_clean"))
        self.tabs.setTabText(4, self._t("tab_meta"))
        self.tabs.setTabText(5, self._t("tab_regex"))
        
        # Text
        self.lbl_find.setText(self._t("find_label"))
        self.lbl_replace.setText(self._t("replace_label"))
        self.chk_case.setText(self._t("case_sensitive"))
        self.chk_regex.setText(self._t("use_regex"))
        self.in_find.setPlaceholderText(self._t("placeholder_find"))
        self.in_replace.setPlaceholderText(self._t("replace_label").replace(":", "..."))
        
        # Case
        idx = self.combo_case.currentIndex()
        self.combo_case.clear()
        self.combo_case.addItems([
            self._t("case_none"), self._t("case_lower"), self._t("case_upper"),
            self._t("case_title"), self._t("case_camel"), self._t("case_snake"), self._t("case_kebab")
        ])
        self.combo_case.setCurrentIndex(max(0, idx))
        
        # Additions
        self.chk_pos_suffix.setText(self._t("pos_suffix"))
        self.lbl_add_sep.setText(self._t("add_sep"))
        self.lbl_add_text.setText(self._t("add_text"))
        self.chk_add_date.setText(self._t("add_date"))
        self.chk_add_time.setText(self._t("add_time"))
        self.chk_add_num.setText(self._t("add_num"))
        self.lbl_num_start.setText(self._t("num_start"))
        self.lbl_num_step.setText(self._t("num_step"))
        self.lbl_num_digits.setText(self._t("num_digits"))
        
        # Clean
        self.chk_clean_tr.setText(self._t("clean_turkish"))
        self.chk_clean_sp.setText(self._t("clean_spaces"))
        self.chk_clean_os.setText(self._t("clean_os_chars"))
        self.lbl_trim_start.setText(self._t("trim_start"))
        self.lbl_trim_end.setText(self._t("trim_end"))
        self.lbl_trim_between.setText(self._t("trim_between"))
        
        # Meta
        self.lbl_meta_help.setText(self._t("meta_help"))
        self.lbl_meta_format.setText(self._t("meta_format"))
        self.in_meta_format.setPlaceholderText(self._t("placeholder_meta"))
        if not HAS_MUTAGEN:
            self.tabs.widget(4).setToolTip(self._t("mutagen_required"))
            
        # Regex
        self.lbl_regex_pat.setText(self._t("regex_pattern"))
        self.lbl_regex_rep.setText(self._t("regex_replace"))
        
        self.lbl_status.setText(self._t("status_ready", count=len(self.files)))
        self._lang_menu.setTitle(self._t("menu_language"))

    # ── Logic & Events ────────────────────────────────────────────────────────

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
            if r < len(self.files):
                del self.files[r]
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
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        act_remove = menu.addAction(self._t("menu_remove"))
        act_remove.triggered.connect(self._remove_highlighted)
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
        
        is_suffix = self.chk_pos_suffix.isChecked()
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
            has_conflict = False
            while key in new_names_set or (os.path.exists(target_path) and key != f['path'].lower()):
                has_conflict = True
                name = f"{original_base}_{counter}{original_ext}"
                target_path = os.path.join(target_dir, name)
                key = target_path.lower() if platform.system() == "Windows" else target_path
                counter += 1
                
            if has_conflict:
                f['new_name'] = name
                item_new.setText(name)
                item_new.setForeground(QColor(255, 60, 60))
            new_names_set.add(key)
            
        self.lbl_status.setText(self._t("status_ready", count=len(self.files)))
        self.table.blockSignals(False)

    def _start_rename(self):
        if not self.files: return
        rename_map = {}
        for f in self.files:
            if f['old_name'] != f['new_name']:
                rename_map[f['path']] = f['new_name']
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
    window = YNRename()
    window.show()
    sys.exit(app.exec_())
