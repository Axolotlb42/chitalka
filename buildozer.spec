[app]
# (основные метаданные)
title = Chitalka
package.name = chitalka
package.domain = org.axolotlb42
source.dir = .
source.include_exts = py,kv,png,jpg,txt,json,pdf
version = 0.1

# Используемые пакеты
# ВАЖНО: PyMuPDF может быть проблемой при сборке для Android. 
# Если возникают ошибки, временно уберите pymupdf и используйте встроенный PDF Reader Android.
requirements = python3,kivy,pymupdf

# Разрешения для доступа к файловой системе, необходимы для работы с PDF папкой Books
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# Ориентация экрана (sensor = автоматический поворот по датчику)
orientation = portrait

# Полноэкранный режим (1 = yes, 0 = no)
fullscreen = 0

# Параметры Android SDK/NDK
android.api = 33
android.minapi = 21
android.ndk = 25b

# Архитектуры процессоров
android.archs = armeabi-v7a,arm64-v8a

# Логирование (0 - выключено, 1 - критическое, 2 - всё)
log_level = 2

# Отключаем использование OGG звука если оно не нужно
ogg_vorbis = no

[buildozer]
# Директория для сборки
build_dir = ./.buildozer

# Лог файл сборки
log_filename = buildozer.log

# Уровень логирования (debug, info, warning, error, critical)
log_level = 2

# Профиль сборки (debug или release)
profile = debug
