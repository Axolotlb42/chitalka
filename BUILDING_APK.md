# Инструкция по сборке APK для Android

## Используемые инструменты

- **Buildozer** - автоматизирует сборку APK из Python кода Kivy
- **Android SDK** - инструменты разработки для Android
- **Android NDK** - натив разработка для Android

## Предварительные требования

1. **Python 3.9+** на вашей системе
2. **Java JDK** (желательно версия 11+)
   - Проверить: `java -version`
3. **Buildozer**
   ```bash
   pip install buildozer
   ```
4. **Android SDK и NDK** - Buildozer может загрузить их автоматически

## Проверка конфигурации buildozer.spec

Основные параметры уже настроены:
- ✅ **android.api = 33** - целевая версия Android API
- ✅ **android.minapi = 21** - минимальная версия Android (API 21 = Android 5.0)
- ✅ **android.ndk = 25b** - версия NDK
- ✅ **android.archs = armeabi-v7a, arm64-v8a** - поддержка процессоров ARM (охватывает ~99% устройств)
- ✅ **android.permissions** - все необходимые разрешения на доступ к файлам
- ✅ **android.orientation = sensor** - автоматический поворот экрана

## Команды для сборки

### 1. Инициализация (первый раз)
```bash
buildozer android debug
```
Buildozer автоматически скачает Android SDK, NDK и соберет приложение.

**Время:** первый раз может занять 30-60 минут.

### 2. Пересборка (после изменений кода)
```bash
buildozer android debug -- --no-update
```
Флаг `--no-update` пропустит переготовку виртуального окружения.

### 3. Создание Release-версии (для загрузки в Google Play)
```bash
buildozer android release
```
Потребует ключ для подписи (см. раздел ниже).

## ⚠️ Известные проблемы с PyMuPDF

### Проблема: ошибка при сборке PyMuPDF
**Решение 1:** Убедитесь что у вас установлены инструменты разработки на Windows:
- Visual C++ Build Tools
- Windows SDK

**Решение 2 (временное):** Временно уберите PyMuPDF из requirements и используйте встроенный Reader Android:
```ini
# В buildozer.spec:
requirements = python3,hostpython3,kivy
# PyMuPDF будет закомментирован временно
```

Затем в `main.py` замените рендеринг PDF на открытие через Intent встроенного приложения.

**Решение 3:** Используйте предскомпилированный PyMuPDF из репозитория p4a.

## Размер APK

Приблизительные размеры:
- **Без PyMuPDF:** 50-80 MB
- **С PyMuPDF:** 150-200 MB

## Установка на устройство

### Через ADB (Android Debug Bridge)
```bash
# Подключить телефон и включить USB Debug
adb install -r bin/chitalka-0.1-debug.apk
```

### Ручная установка
1. Скопировать `bin/chitalka-0.1-debug.apk` на компьютер
2. Передать файл на телефон
3. Открыть файл на телефоне и установить

## Запуск приложения на устройстве

После установки приложение будет доступно в меню "Приложения" с названием "Chitalka".

Первый запуск объект:
1. Создаст папку `Books` во внутреннем хранилище
2. Попросит разрешение на доступ к файлам
3. Будет готово к использованию

## Release сборка (для Google Play Store)

### 1. Создание ключа подписи
```bash
keytool -genkey -v -keystore chitalka.keystore -keyalg RSA -keysize 2048 -validity 10000 -alias chitalka
```

### 2. Добавить в buildozer.spec:
```ini
[app]
android.release_artifact = aab

[buildozer]
android.keystore = 1
android.keystore_alias = chitalka
android.keystore_path = ./chitalka.keystore
```

### 3. Собрать release версию
```bash
buildozer android release
```

## Рекомендации

1. **Тестируйте на десктопе** перед сборкой для Android
2. **Используйте эмулятор Android** для быстрого тестирования
3. **Проверяйте размер APK** - каждый мегабайт важен
4. **Документируйте зависимости** - если добавляете новые пакеты в requirements
5. **Версионируйте кода** - обновляйте version в buildozer.spec

## Полезные команды

```bash
# Очистить сборку (если что-то сломалось)
buildozer android clean

# Полностью очистить (нужно переготавливать всё)
buildozer android distclean

# Завеси логи сборки
cat buildozer.log
```

## Дополнительные ресурсы

- [Официальная документация Buildozer](https://buildozer.readthedocs.io/)
- [Kivy на Android](https://kivy.org/doc/stable/guide/android.html)
- [Android Developer Docs](https://developer.android.com/)
