# Читалка для школьных учебников на Kivy + PyMuPDF
# Объединил предыдущие версии: список без расширений, предотвращение дубликатов, кеширование,
# и добавил масштаб (увеличение/уменьшение).
#
# Требования:
#  - kivy
#  - PyMuPDF (fitz)
# Запуск на десктопе: python main.py
# Для Android: собрать через buildozer/ p4a, добавить pymupdf в requirements (возможны сложности со сборкой).

import os
import threading
import shutil
from functools import partial

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.utils import platform
from kivy.core.window import Window as KivyWindow

# Попытка импортировать файловый диалог
try:
    from kivy.uix.filechooser import FileChooserListView
    from kivy.uix.boxlayout import BoxLayout as KivyBoxLayout
    from kivy.uix.button import Button as KivyButton
    HAVE_FILECHOOSER = True
except Exception:
    HAVE_FILECHOOSER = False

# Тема приложения
class Theme:
    # Светлая тема
    LIGHT = {
        'bg_primary': (0.95, 0.95, 0.95, 1),  # Светлый фон
        'bg_secondary': (0.9, 0.9, 0.9, 1),   # Более тёмный свет
        'text_primary': (0.1, 0.1, 0.1, 1),   # Чёрный текст
        'text_secondary': (0.3, 0.3, 0.3, 1), # Серый текст
        'button_bg': (0.85, 0.85, 0.85, 1),   # Кнопка светлая
    }
    
    # Тёмная тема
    DARK = {
        'bg_primary': (0.15, 0.15, 0.15, 1),  # Тёмный фон
        'bg_secondary': (0.2, 0.2, 0.2, 1),   # Более светлый темный
        'text_primary': (0.95, 0.95, 0.95, 1), # Белый текст
        'text_secondary': (0.7, 0.7, 0.7, 1),  # Светлый серый
        'button_bg': (0.25, 0.25, 0.25, 1),    # Кнопка тёмная
    }

# Попытка импортировать PyMuPDF (fitz)
try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except Exception:
    HAVE_FITZ = False

KV = """
ScreenManager:
    MainScreen:
    ReaderScreen:

<MainScreen>:
    name: 'main'
    BoxLayout:
        orientation: 'vertical'
        padding: 8
        spacing: 8

        Label:
            text: 'Выберите учебник (папка Books)'
            size_hint_y: None
            height: '48dp'
            font_size: '18sp'

        ScrollView:
            do_scroll_x: False

            GridLayout:
                id: books_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                row_default_height: '48dp'
                spacing: 6
                padding: 4

        BoxLayout:
            size_hint_y: None
            height: '48dp'
            spacing: 8

            Button:
                text: 'Обновить список'
                on_release: app.scan_books()

            Button:
                text: 'Добавить учебник'
                on_release: app.add_book()

            Button:
                text: 'Тема'
                on_release: app.toggle_theme()

            Button:
                text: 'О приложении'
                on_release: app.show_info()

            Button:
                text: 'Выход'
                on_release: app.stop()

<ReaderScreen>:
    name: 'reader'
    BoxLayout:
        orientation: 'vertical'
        spacing: 8
        padding: 6

        BoxLayout:
            size_hint_y: None
            height: '48dp'
            spacing: 8

            Button:
                text: '←'
                size_hint_x: None
                width: '48dp'
                on_release: root.prev_page()

            Label:
                id: title_label
                text: ''
                halign: 'center'
                valign: 'middle'
                text_size: self.size

            Button:
                text: '→'
                size_hint_x: None
                width: '48dp'
                on_release: root.next_page()

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: 8

            Button:
                text: '-'
                size_hint_x: None
                width: '48dp'
                on_release: root.zoom_out()

            Label:
                id: zoom_label
                text: '100%'
                size_hint_x: None
                width: '80dp'
                halign: 'center'
                valign: 'middle'
                text_size: self.size

            Button:
                text: '+'
                size_hint_x: None
                width: '48dp'
                on_release: root.zoom_in()

            Widget:

            Button:
                text: 'Назад к списку'
                size_hint_x: None
                width: '140dp'
                on_release:
                    app.root.transition.direction = 'right'
                    app.root.current = 'main'

        BoxLayout:
            orientation: 'horizontal'
            padding: 0
            spacing: 0

            Widget:

            ScrollView:
                size_hint_x: None
                width: 600
                canvas.before:
                    Color:
                        rgba: app.current_theme['bg_primary']
                    Rectangle:
                        pos: self.pos
                        size: self.size

                BoxLayout:
                    id: image_box
                    orientation: 'vertical'
                    size_hint: None, None
                    size: page_image.size
                    canvas.before:
                        Color:
                            rgba: app.current_theme['bg_primary']
                        Rectangle:
                            pos: self.pos
                            size: self.size

                    Image:
                        id: page_image
                        fit_mode: 'scale-down'
                        source: ''
                        size_hint: None, None
                        size: self.texture_size if self.texture else (400, 600)

            Widget:

        BoxLayout:
            size_hint_y: None
            height: '48dp'
            spacing: 8

            TextInput:
                id: page_input
                hint_text: 'Номер страницы'
                input_filter: 'int'
                multiline: False
                on_text_validate: root.go_to_page(self.text)

            Button:
                text: 'Перейти'
                size_hint_x: None
                width: '100dp'
                on_release: root.go_to_page(page_input.text)
"""
# Список возможных путей для папки Books (адаптируется под платформу)


# def find_books_dirs():
#     dirs = []
#     if platform == 'android':
#         # На Android используем внутреннее хранилище приложения
#         app = App.get_running_app()
#         if app:
#             books_dir = os.path.join(app.user_data_dir, 'Books')
#             os.makedirs(books_dir, exist_ok=True)
#             dirs.append(books_dir)
#     else:
#         # На десктопе создаём и используем папку Books рядом с программой
#         books_dir = os.path.join(os.getcwd(), 'Books')
#         os.makedirs(books_dir, exist_ok=True)
#         dirs.append(books_dir)
#         # Также проверим /sdcard если существует (для совместимости)
#         if os.path.isdir('/sdcard/Books'):
#             dirs.append('/sdcard/Books')
#     return dirs

def find_books_dirs():
    dirs = []
    # Путь внутри установленного APK (там, где лежит main.py)
    internal_books = os.path.join(os.path.dirname(__file__), 'Books')
    if os.path.exists(internal_books):
        dirs.append(internal_books)
    
    if platform == 'android':
        app = App.get_running_app()
        if app:
            # Путь для учебников, которые пользователь добавит сам
            user_dir = os.path.join(app.user_data_dir, 'Books')
            os.makedirs(user_dir, exist_ok=True)
            dirs.append(user_dir)
    else:
        # Для десктопа
        desktop_books = os.path.join(os.getcwd(), 'Books')
        os.makedirs(desktop_books, exist_ok=True)
        dirs.append(desktop_books)
        
    return dirs

def find_pdf_files():
    found = []
    seen = set()
    for d in find_books_dirs():
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith('.pdf'):
                    full = os.path.join(root, f)
                    if full not in seen:
                        seen.add(full)
                        found.append(full)
    return found


class MainScreen(Screen):
    pass


class ReaderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pdf_path = None
        self.doc = None
        self.page_count = 0
        self.current_page = 0
        self.cache_dir = None
        # zoom — множитель рендеринга (1.0 = 100% - учебник занимает весь экран)
        self.zoom = 1.0
        self.zoom_step = 0.1
        self.zoom_min = 0.5
        self.zoom_max = 3.0
        self._render_lock = threading.Lock()
        self._base_image_size = (400, 600)  # базовый размер при зуме 1.0
        # Для отслеживания касаний/мыши для листания и перемещения
        self._touch_start_x = None
        self._touch_start_y = None
        self._touch_threshold = 50  # минимальное расстояние для листания (пиксели)
        self._is_dragging = False  # флаг для отслеживания движения
        # Переменные для pinch-zoom жеста
        self._touch_points = {}  # Словарь {touch_id: (x, y)} для отслеживания нескольких пальцев
        self._initial_distance = None  # Начальное расстояние между двумя пальцами
        self._initial_zoom = None  # Начальный zoom при начале жеста

    def open_pdf(self, pdf_path):
        self.pdf_path = pdf_path
        self.cache_dir = os.path.join(App.get_running_app().user_data_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        # поставить заголовок имя файла (без расширения)
        display_name = os.path.splitext(os.path.basename(pdf_path))[0]
        self.ids.title_label.text = display_name
        # Сбросить текущий документ
        self.doc = None
        self.page_count = 0
        self.current_page = 0
        # начальный zoom (1.0 = 100% - учебник занимает весь экран)
        self.zoom = 1.0
        self._update_zoom_label()
        if not HAVE_FITZ:
            App.get_running_app().show_popup('Ошибка', 'PyMuPDF (fitz) не установлен. Нельзя открыть PDF внутри приложения.')
            return

        # Открытие документа в отдельном потоке, чтобы не блокировать UI
        threading.Thread(target=self._open_doc_thread, daemon=True).start()

    def _open_doc_thread(self):
        try:
            doc = fitz.open(self.pdf_path)
            self.doc = doc
            self.page_count = doc.page_count
            self.current_page = 0
            # Рендер первой страницы
            self._render_and_show(self.current_page, self.zoom)
        except Exception as e:
            App.get_running_app().show_popup('Ошибка', f'Не удалось открыть {os.path.basename(self.pdf_path)}:\n{e}')

    def _page_cache_path(self, page_num, zoom):
        name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        zoom_key = int(zoom * 100)  # чтобы избежать плавающей точки в имени
        filename = f'{name}_p{page_num}_z{zoom_key}.png'
        # безопасное имя файла (удаляем недопустимые символы)
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-', '(', ')')).rstrip()
        return os.path.join(self.cache_dir, filename)

    def _render_and_show(self, page_num, zoom):
        # Не позволяем двум потокам рендерить одновременно один и тот же документ
        with self._render_lock:
            if not self.doc:
                return
            cache_path = self._page_cache_path(page_num, zoom)
            if not os.path.exists(cache_path):
                try:
                    page = self.doc.load_page(page_num)
                    mat = fitz.Matrix(zoom, zoom)
                    # Без альфа-канала (альфа=False) уменьшает размер
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    pix.save(cache_path)
                except Exception as e:
                    App.get_running_app().show_popup('Ошибка', f'Ошибка рендеринга страницы: {e}')
                    return
            # Установить источник изображения в UI в главном потоке
            # Обновляем current_page и label в _set_image_source
            self._set_image_source(cache_path)

    @mainthread
    def _set_image_source(self, path):
        # Перед назначением источника показываем текущую страницу / общее количество
        # title_label уже содержит имя файла; дополним его информацией о странице
        base = os.path.splitext(os.path.basename(self.pdf_path))[0] if self.pdf_path else ''
        page_info = f"{self.current_page + 1}/{self.page_count}" if self.page_count else ""
        self.ids.title_label.text = f"{base} — {page_info}" if page_info else base
        self.ids.page_image.source = path
        self.ids.page_image.reload()
        self.ids.page_input.text = str(self.current_page + 1)
        # Обновляем размер изображения на основе зума
        self._update_image_size()

    @mainthread
    def _update_image_size(self):
        """Обновить размер Image в зависимости от текущего зума"""
        try:
            page_image = self.ids.page_image
            if page_image.texture:
                # Вычисляем новый размер на основе текстуры и зума
                texture_width = page_image.texture.width
                texture_height = page_image.texture.height
                # Масштабируем размер на основе зума
                scaled_width = int(texture_width * self.zoom / 2.0)
                scaled_height = int(texture_height * self.zoom / 2.0)
                page_image.size = (scaled_width, scaled_height)
        except Exception:
            pass

    def next_page(self):
        if not self.doc:
            return
        if self.current_page + 1 < self.page_count:
            self.current_page += 1
            threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()

    def prev_page(self):
        if not self.doc:
            return
        if self.current_page > 0:
            self.current_page -= 1
            threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()

    def go_to_page(self, page_text):
        if not self.doc:
            return
        try:
            p = int(page_text) - 1
            if p < 0 or p >= self.page_count:
                App.get_running_app().show_popup('Ошибка', f'Номер страницы вне диапазона (1 — {self.page_count})')
                return
            self.current_page = p
            threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()
        except ValueError:
            App.get_running_app().show_popup('Ошибка', 'Введите корректный номер страницы.')

    def zoom_in(self):
        if not self.doc:
            return
        new_zoom = round(self.zoom + self.zoom_step, 2)
        if new_zoom > self.zoom_max:
            new_zoom = self.zoom_max
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self._update_zoom_label()
            self._update_image_size()
            threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()

    def zoom_out(self):
        if not self.doc:
            return
        new_zoom = round(self.zoom - self.zoom_step, 2)
        if new_zoom < self.zoom_min:
            new_zoom = self.zoom_min
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self._update_zoom_label()
            self._update_image_size()
            threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()

    @mainthread
    def _update_zoom_label(self):
        percent = int(self.zoom * 100)
        try:
            self.ids.zoom_label.text = f"{percent}%"
        except Exception:
            pass

    def _get_distance(self, p1, p2):
        """Вычисляет расстояние между двумя точками"""
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def on_touch_down(self, touch):
        """Обработчик нажатия мыши/касания"""
        # Добавляем новую точку касания в словарь
        self._touch_points[touch.uid] = (touch.x, touch.y)
        
        # Если это первый палец
        if len(self._touch_points) == 1:
            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
            self._is_dragging = False
        # Если это второй палец (начинаем жест pinch-zoom)
        elif len(self._touch_points) == 2:
            points = list(self._touch_points.values())
            self._initial_distance = self._get_distance(points[0], points[1])
            self._initial_zoom = self.zoom
        
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """Обработчик движения мыши/касания"""
        # Обновляем позицию касания
        if touch.uid in self._touch_points:
            self._touch_points[touch.uid] = (touch.x, touch.y)
        
        # Если два пальца - обрабатываем pinch-zoom
        if len(self._touch_points) == 2 and self._initial_distance is not None:
            points = list(self._touch_points.values())
            current_distance = self._get_distance(points[0], points[1])
            
            # Вычисляем коэффициент масштабирования
            zoom_factor = current_distance / self._initial_distance
            new_zoom = round(self._initial_zoom * zoom_factor, 2)
            
            # Ограничиваем zoom в пределах допустимых значений
            if new_zoom < self.zoom_min:
                new_zoom = self.zoom_min
            elif new_zoom > self.zoom_max:
                new_zoom = self.zoom_max
            
            # Применяем новый zoom
            if new_zoom != self.zoom:
                self.zoom = new_zoom
                self._update_zoom_label()
                self._update_image_size()
                # Рендерим страницу с новым масштабом в фоне
                threading.Thread(target=self._render_and_show, args=(self.current_page, self.zoom), daemon=True).start()
        # Если один палец - обрабатываем обычное движение
        elif len(self._touch_points) == 1 and self._touch_start_x is not None:
            delta_x = touch.x - self._touch_start_x
            delta_y = touch.y - self._touch_start_y
            
            # Определяем, действительно ли это движение (а не маленькие дрожания)
            if abs(delta_x) > 5 or abs(delta_y) > 5:
                self._is_dragging = True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Обработчик отпускания мыши/касания"""
        # Удаляем точку касания из словаря
        if touch.uid in self._touch_points:
            del self._touch_points[touch.uid]
        
        # Сбрасываем переменные при отпускании всех пальцев
        if len(self._touch_points) == 0:
            self._touch_start_x = None
            self._touch_start_y = None
            self._is_dragging = False
            self._initial_distance = None
            self._initial_zoom = None
        
        return super().on_touch_up(touch)


class ReaderApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_dark_theme = True  # Начинаем с тёмной темы
        self.current_theme = Theme.DARK

    def build(self):
        self.title = 'Читалка'
        self.sm = Builder.load_string(KV)
        # Гарантируем создание папки Books при запуске
        find_books_dirs()
        # Уменьшаем минимальный DPI на десктопе, чтобы окно было удобнее
        try:
            if not hasattr(self, 'android'):
                Window.minimum_width = 300
                Window.minimum_height = 400
        except Exception:
            pass
        # Установим начальную тёмную тему
        self.apply_theme()
        # Первичная сканировка
        self.scan_books()
        # Попытка запросить разрешения на Android (если возможно)
        self.request_android_permissions()
        return self.sm

    def toggle_theme(self):
        """Переключает между тёмной и светлой темой"""
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        """Применяет текущую тему к приложению"""
        if self.is_dark_theme:
            self.current_theme = Theme.DARK
            KivyWindow.clearcolor = (0.1, 0.1, 0.1, 1)
        else:
            self.current_theme = Theme.LIGHT
            KivyWindow.clearcolor = (0.98, 0.98, 0.98, 1)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.9, 0.6))
        popup.open()

    def show_info(self):
        msg = ("Читалка (Kivy + PyMuPDF).\n\n"
               "Поместите pdf-файлы в папку Books рядом с приложением (десктоп) или во внутреннее хранилище приложения (Android).\n"
               "Для работы внутри приложения требуется PyMuPDF (fitz).\n"
               "Управление: кнопки вперед/назад, ввод номера страницы, масштаб +/-.\n")
        self.show_popup('О приложении', msg)

    def scan_books(self):
        books = find_pdf_files()
        books_list = self.sm.get_screen('main').ids.books_list
        books_list.clear_widgets()
        if not books:
            books_list.add_widget(Label(text='PDF не найдено в папке Books', size_hint_y=None, height='40dp'))
            return
        # Словарь для учета повторяющихся отображаемых имён
        seen = {}
        for p in sorted(books):
            # Убираем расширение (.pdf) и чистим имя
            display = os.path.splitext(os.path.basename(p))[0]
            display = display.replace('_', ' ').strip()
            # Если уже есть такое отображаемое имя — добавляем суффикс
            if display in seen:
                seen[display] += 1
                display_with_suffix = f"{display} ({seen[display]})"
            else:
                seen[display] = 0
                display_with_suffix = display
            from kivy.uix.button import Button
            b = Button(text=display_with_suffix, size_hint_y=None, height='40dp')
            b.bind(on_release=partial(self.open_book, p))
            books_list.add_widget(b)

    def open_book(self, path, *args):
        # Переходим на экран чтения и открываем PDF
        reader = self.sm.get_screen('reader')
        self.sm.transition = SlideTransition(direction='left')
        self.sm.current = 'reader'
        reader.open_pdf(path)

    def request_android_permissions(self):
        # Попытка запросить runtime permissions для Android 6+
        try:
            # модуль android.permissions доступен в сборках p4a
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE])
        except Exception:
            # не Android или модуль недоступен — молча пропускаем
            pass

    def add_book(self):
        """Открывает диалог для выбора PDF файла и копирует его в папку Books"""
        current_platform = platform
        
        if current_platform == 'android':
            # На Android предлагаем копировать файлы вручную
            books_dirs = find_books_dirs()
            if books_dirs:
                books_path = books_dirs[0]
                msg = (f"На Android скопируйте PDF файлы в папку Books вручную.\n\n"
                       f"Путь: {books_path}\n\n"
                       f"Используйте файловый менеджер для копирования файлов.")
            else:
                msg = "На Android скопируйте PDF файлы в папку Books вручную через файловый менеджер."
            self.show_popup('Добавление учебника', msg)
            return
        
        # На десктопе используем диалог выбора файла
        if not HAVE_FILECHOOSER:
            self.show_popup('Ошибка', 'FileChooser недоступен на этой платформе')
            return

        # Получаем папку Books
        books_dirs = find_books_dirs()
        if not books_dirs:
            self.show_popup('Ошибка', 'Папка Books не найдена')
            return

        target_dir = books_dirs[0]

        # Создаем диалог выбора файла
        content = KivyBoxLayout(orientation='vertical')
        filechooser = FileChooserListView(filters=['*.pdf'])
        content.add_widget(filechooser)

        # Кнопки для диалога
        button_layout = KivyBoxLayout(size_hint_y=0.1, spacing=10)
        
        popup = Popup(title='Выберите PDF файл', content=content, size_hint=(0.9, 0.9))

        def select_file(*args):
            if filechooser.selection:
                file_path = filechooser.selection[0]
                try:
                    # Копируем файл в папку Books
                    file_name = os.path.basename(file_path)
                    dest_path = os.path.join(target_dir, file_name)
                    shutil.copy2(file_path, dest_path)
                    self.show_popup('Успех', f'Учебник добавлен: {file_name}')
                    self.scan_books()  # Обновляем список
                    popup.dismiss()
                except Exception as e:
                    self.show_popup('Ошибка', f'Не удалось добавить файл: {e}')
            else:
                self.show_popup('Ошибка', 'Пожалуйста, выберите файл')

        def cancel(*args):
            popup.dismiss()

        select_btn = KivyButton(text='Выбрать', size_hint_x=0.5)
        cancel_btn = KivyButton(text='Отмена', size_hint_x=0.5)
        
        select_btn.bind(on_press=select_file)
        cancel_btn.bind(on_press=cancel)

        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        content.add_widget(button_layout)

        popup.open()


if __name__ == '__main__':
    if not HAVE_FITZ:
        print("Внимание: PyMuPDF (fitz) не найден. Приложение запустится, но PDF не откроются внутри приложения.")
    ReaderApp().run()