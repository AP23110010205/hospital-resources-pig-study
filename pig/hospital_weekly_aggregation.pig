
cleaned = LOAD 'output/hospital_cleaned/part-m-00000'
USING PigStorage('\t')
AS (
    hospital_pk:chararray,
    collection_week:chararray,
    state:chararray,
    hospital_name:chararray,
    total_beds:double,
    occupied_beds:double,
    occupancy_rate:double
);

grouped = GROUP cleaned BY (state, collection_week);

weekly_summary = FOREACH grouped GENERATE
    group.state AS state,
    group.collection_week AS collection_week,
    COUNT(cleaned) AS hospital_count,
    SUM(cleaned.total_beds) AS total_beds,
    SUM(cleaned.occupied_beds) AS occupied_beds,
    AVG(cleaned.occupancy_rate) AS average_occupancy_rate;

STORE weekly_summary INTO 'output/weekly_state_summary'
USING PigStorage(',');
