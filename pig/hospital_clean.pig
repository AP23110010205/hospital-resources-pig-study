
raw = LOAD 'dataset/hospital_2023.tsv'
USING PigStorage('\t')
AS (
    hospital_pk:chararray,
    collection_week:chararray,
    state:chararray,
    hospital_name:chararray,
    total_beds:double,
    occupied_beds:double
);

valid = FILTER raw BY
    hospital_pk != 'hospital_pk'
    AND total_beds IS NOT NULL
    AND occupied_beds IS NOT NULL
    AND total_beds > 0
    AND occupied_beds >= 0
    AND occupied_beds <= total_beds;

cleaned = FOREACH valid GENERATE
    hospital_pk,
    collection_week,
    state,
    hospital_name,
    total_beds,
    occupied_beds,
    (occupied_beds / total_beds) AS occupancy_rate;

STORE cleaned INTO 'output/hospital_cleaned'
USING PigStorage('\t');
