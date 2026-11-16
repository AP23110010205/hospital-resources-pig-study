hospitals = LOAD 'dataset/hospital_sample.csv'
USING PigStorage(',')
AS (hospital:chararray, total_beds:int, occupied_beds:int, available_staff:int);

metrics = FOREACH hospitals GENERATE
    hospital,
    total_beds,
    occupied_beds,
    available_staff,
    (double)occupied_beds / total_beds AS occupancy_rate;

DUMP metrics;
