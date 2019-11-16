CREATE TABLE raw.event_data_{date}
(
    ts UInt64,
    userId String,
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
    gender LowCardinality(String),
    artist String,
    song String,
    length Float32
)
ENGINE=Log()