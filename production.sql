-- Создаем отдельную БД для сырья
CREATE DATABASE raw;

-- Продакшн-таблица в дефолте
/* 
 * Движок: ReplacingMergeTree: надеемся, что схема заливки не даст нам дублей, но будем за этим следить
 * Партиционирование по месяцам. Классика: данных сравнительно немного, чтобы делать партиции по дням.
 * Сэмпл по не очень мощному хэшу по userId: добиваемся более равномерного распределения в сэмпле
 * Сортировка в первую очередь по юзерам: они наша главная сущность для анализа в таблице. 
 * Дальше по убыванию размера сущности: день-сессия-время-id элемента сессии.
 * Не уверен, что оставлял бы artist/song/location/lastName/firstName в прод-таблице. 
 * Нужно хранить кучу стрингов тогда, когда это не необходимо.
 * Можно было бы спокойно жить с id с словарями – сомневаюсь, что нужно будет делать группировки по всем артистам/песням сразу
 * Плюс в LowCardinality запихивать сущности, в которых точно будет много различных значениий не стоит.
 * Группировка по String всегда будет проигрывать группировке по Int.
 * userAgent лучше парсить на бэке и отдавать что-то более группабельное, например, браузер, ОС, "старый" или нет и т.д.
 * Все, что имело смысл делать LowCardinality – делал в нем.
 * length в Int преобразовывать не стал: без потери точности значения влезают только в UInt64. 
 * Производительность зависит больше от бит, чем типа данных (https://www.percona.com/blog/2019/02/15/clickhouse-performance-uint32-vs-uint64-vs-float32-vs-float64/)
 *
 * Добавляются столбцы: 
 * dt (toDate(ts / 1000)) – дата события для партиции и удобной группировки
 * time (toDateTime(ts / 1000)) – секунда события для группировок по времени
 * Аналогично с registrationDate и registrationTime
*/
CREATE TABLE default.event_data (
    dt Date,
    time DateTime,
    ts UInt64,
    userId UInt32,
    sessionId UInt32,
    page LowCardinality(String),
    auth LowCardinality(String),
    method LowCardinality(String),
    status UInt16,
    level LowCardinality(String),
    itemInSession UInt16,
    location String,
    userAgent String,
    lastName String,
    firstName String,
    registration UInt64,
    registrationDate Date,
    registrationTime DateTime,
    gender LowCardinality(String),
    artist String,
    song String,
    length Float32
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(dt)
SAMPLE BY intHash32(userId)
ORDER BY (intHash32(userId), dt, intHash32(sessionId), ts, itemInSession)
