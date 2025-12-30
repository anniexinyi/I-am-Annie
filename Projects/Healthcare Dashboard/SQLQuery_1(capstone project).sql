




CREATE TABLE Patient (
    P_ID INT PRIMARY KEY,
    PatientName VARCHAR(100),
    PatientAge INT,
    PatientGender VARCHAR(10),
    PatientBirthdate DATE,
    PatientDepartment VARCHAR(100)
);

BULK INSERT Patient FROM 'D:\学习\Pittsburgh\capstone project\patient.csv'
WITH(firstrow = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a')

select * from Patient
drop table Patient

UPDATE Patient
SET PatientDepartment = 
    LTRIM(RTRIM(
        REPLACE(REPLACE(REPLACE(PatientDepartment, CHAR(13), ''), CHAR(10), ''), CHAR(9), '')
    ));

CREATE TABLE Fact_Labtest (
    T_ID INT PRIMARY KEY,            -- Test ID
    P_ID INT,                        -- Patient ID
    D_ID INT,                        -- Doctor ID
    L_ID INT,                        -- Lab test ID (foreign key to Fact_Test)
    testdate DATE,                  -- Date of the test
    testresult VARCHAR(100),       -- Result of the test
    FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
    FOREIGN KEY (D_ID) REFERENCES Doctor(D_ID),
    FOREIGN KEY (L_ID) REFERENCES Fact_Test(L_ID)  -- Correct FK reference
);

-- Step 1: First, get 1 test per patient matched with any doctor in the same department
WITH UniquePatientTests AS (
    SELECT 
        p.P_ID,
        d.D_ID,
        t.L_ID,
        DATEADD(DAY, ABS(CHECKSUM(NEWID())) % 90, '2025-01-01') AS testdate,
        CASE 
            WHEN ABS(CHECKSUM(NEWID())) % 2 = 0 THEN 'Positive'
            ELSE 'Negative'
        END AS testresult,
        ROW_NUMBER() OVER (PARTITION BY p.P_ID ORDER BY NEWID()) AS PatientRow
    FROM 
        Patient p
    JOIN Doctor d ON p.PatientDepartment = d.DoctorDepartment
    JOIN Fact_Test t ON d.DoctorDepartment = t.TestDepartment
),
-- Step 2: Only keep one row per patient
LimitedPatients AS (
    SELECT * FROM UniquePatientTests
    WHERE PatientRow = 1
),
-- Step 3: Limit each doctor to a maximum of 5 patients
DoctorLimited AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY D_ID ORDER BY NEWID()) AS DoctorPatientRow
    FROM LimitedPatients
),
-- Step 4: Only keep up to 5 patients per doctor
FinalSelection AS (
    SELECT * FROM DoctorLimited
    WHERE DoctorPatientRow <= 5
)
-- Step 5: Insert the result
INSERT INTO Fact_Labtest (T_ID, P_ID, D_ID, L_ID, testdate, testresult)
SELECT 
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS T_ID,
    P_ID,
    D_ID,
    L_ID,
    testdate,
    testresult
FROM FinalSelection;


-- Creating Fact_Test table
CREATE TABLE Fact_Test (
    L_ID INT PRIMARY KEY,
    LOINC VARCHAR(50), 
    testname VARCHAR(300),
    TestDepartment VARCHAR(100)
);

BULK INSERT Fact_Test
FROM 'D:\学习\Pittsburgh\capstone project\Test.csv'
WITH (
    FIRSTROW = 2, 
    FIELDTERMINATOR = ',', 
    ROWTERMINATOR = '0x0a'
);

UPDATE Fact_Test
SET TestDepartment = 
    LTRIM(RTRIM(
        REPLACE(REPLACE(REPLACE(TestDepartment, CHAR(13), ''), CHAR(10), ''), CHAR(9), '')
    ));

select * from Fact_Labtest
select * from Fact_Test
drop table Fact_Labtest
drop table Fact_Test

CREATE TABLE Fact_Prescription (
    R_ID INT PRIMARY KEY,
    P_ID INT,
    D_ID INT,
    Quantity INT,
    Prescriptionprice INT,
    FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
    FOREIGN KEY (D_ID) REFERENCES Doctor(D_ID)
);

WITH PositiveTests AS (
    SELECT 
        r.P_ID,
        r.D_ID,
        r.L_ID,
        t.LOINC,
        t.testname,
        r.testresult
    FROM Fact_Labtest r
    JOIN Fact_Test t ON r.L_ID = t.L_ID
    WHERE r.testresult = 'Positive'
      AND t.testname IN (
          'HIV 1+2 Ab [Presence] in Serum Plasma or Blood by Rapid Immunoassay',
          'Hepatitis B virus surface Ag [Presence] in Serum Plasma or Blood by Rapid Immunoassay',
          'Influenza virus A RNA [Presence] in Upper Respiratory Specimen by NAA with Probe Detection',
          'Amphetamines [Presence] in Urine by Screen Method',
          'Ethanol [Presence] in Serum or Plasma by Screen Method'
      )
)
INSERT INTO Fact_Prescription (R_ID, P_ID, D_ID, Quantity, Prescriptionprice)
SELECT 
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS R_ID,
    pt.P_ID,
    pt.D_ID,
    ABS(CHECKSUM(NEWID())) % 3 + 1 AS Quantity,
    CASE 
        WHEN pt.testname LIKE '%HIV%' THEN 120
        WHEN pt.testname LIKE '%Hepatitis B%' THEN 120
        WHEN pt.testname LIKE '%Influenza%' THEN 95
        WHEN pt.testname LIKE '%Amphetamines%' THEN 70
        WHEN pt.testname LIKE '%Ethanol%' THEN 110
        ELSE 50
    END AS Prescriptionprice
FROM PositiveTests pt
ORDER BY (SELECT NULL)
OFFSET 0 ROWS FETCH NEXT 500 ROWS ONLY;

SELECT * FROM Fact_Prescription
drop table Fact_Prescription

CREATE TABLE Fact_Drug (
    C_ID INT PRIMARY KEY,
    P_ID INT,
    LOINC VARCHAR(50),
    drugname VARCHAR(100),
    ndc_code VARCHAR(50),
    testresult VARCHAR(50)
);

INSERT INTO Fact_Drug (C_ID, P_ID, LOINC, drugname, ndc_code, testresult)
SELECT 
    ROW_NUMBER() OVER (ORDER BY NEWID()) AS C_ID,
    r.P_ID,
    t.LOINC,
    CASE 
        WHEN t.testname = 'HIV 1+2 Ab [Presence] in Serum Plasma or Blood by Rapid Immunoassay' THEN 'Tenofovir'
        WHEN t.testname = 'Hepatitis B virus surface Ag [Presence] in Serum Plasma or Blood by Rapid Immunoassay' THEN 'Tenofovir'
        WHEN t.testname = 'Influenza virus A RNA [Presence] in Upper Respiratory Specimen by NAA with Probe Detection' THEN 'Tamiflu'
        WHEN t.testname = 'Amphetamines [Presence] in Urine by Screen Method' THEN 'Lorazepam'
        WHEN t.testname = 'Ethanol [Presence] in Serum or Plasma by Screen Method' THEN 'Naltrexone'
        ELSE NULL
    END AS drugname,
    CASE 
        WHEN t.testname = 'HIV 1+2 Ab [Presence] in Serum Plasma or Blood by Rapid Immunoassay' THEN '16714-0534-01'
        WHEN t.testname = 'Hepatitis B virus surface Ag [Presence] in Serum Plasma or Blood by Rapid Immunoassay' THEN '16714-0534-01'
        WHEN t.testname = 'Influenza virus A RNA [Presence] in Upper Respiratory Specimen by NAA with Probe Detection' THEN '00004-0800-07'
        WHEN t.testname = 'Amphetamines [Presence] in Urine by Screen Method' THEN '00641-6000-10'
        WHEN t.testname = 'Ethanol [Presence] in Serum or Plasma by Screen Method' THEN '65757-0300-01'
        ELSE NULL
    END AS ndc_code,
    r.testresult
FROM Fact_Test t
JOIN Fact_Labtest r ON t.L_ID = r.L_ID
WHERE r.testresult = 'Positive'
AND t.testname IN (
    'HIV 1+2 Ab [Presence] in Serum Plasma or Blood by Rapid Immunoassay',
    'Hepatitis B virus surface Ag [Presence] in Serum Plasma or Blood by Rapid Immunoassay',
    'Influenza virus A RNA [Presence] in Upper Respiratory Specimen by NAA with Probe Detection',
    'Amphetamines [Presence] in Urine by Screen Method',
    'Ethanol [Presence] in Serum or Plasma by Screen Method'
)
ORDER BY NEWID()
OFFSET 0 ROWS FETCH NEXT 500 ROWS ONLY;

select * from Fact_Drug
drop table Fact_Drug

-- Drop old admission table if needed

-- Step 0: Clean up previous temp data
DROP TABLE IF EXISTS #DoctorNursePairs;

CREATE TABLE Fact_Admission ( 
    A_ID INT PRIMARY KEY,
    P_ID INT,
    D_ID INT,
    N_ID INT,
    RoomID INT,
    AdmissionDate DATE,
    DischargeDate DATE,
    FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
    FOREIGN KEY (D_ID) REFERENCES Doctor(D_ID),
    FOREIGN KEY (N_ID) REFERENCES Nurse(N_ID),
    FOREIGN KEY (RoomID) REFERENCES Room(RoomID)
);

-- Step 1: Match doctors and nurses by department
SELECT d.D_ID, n.N_ID, d.DoctorDepartment
INTO #DoctorNursePairs
FROM Doctor d
JOIN Nurse n ON d.DoctorDepartment = n.NurseDepartment;

-- Step 2: Get one positive test per patient
WITH PositiveTests AS (
    SELECT 
        fl.T_ID,
        fl.P_ID,
        fl.D_ID AS TestDoctorID,
        fl.TestDate,
        ROW_NUMBER() OVER (PARTITION BY fl.P_ID ORDER BY NEWID()) AS rn_test
    FROM Fact_Labtest fl
    WHERE fl.testresult = 'Positive'
),
FilteredTests AS (
    SELECT * FROM PositiveTests WHERE rn_test = 1
),

-- Step 3: Assign a nurse (limit 5 patients max)
NurseAssignments AS (
    SELECT 
        ft.*,
        dnp.N_ID,
        dnp.DoctorDepartment,
        ROW_NUMBER() OVER (PARTITION BY dnp.N_ID ORDER BY NEWID()) AS nurse_rn
    FROM FilteredTests ft
    JOIN #DoctorNursePairs dnp ON ft.TestDoctorID = dnp.D_ID
),
LimitedNurseAssignments AS (
    SELECT * FROM NurseAssignments WHERE nurse_rn <= 5
),

-- Step 4: Randomize and calculate Admission/Discharge dates
Numbered AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY NEWID()) AS rn_row
    FROM LimitedNurseAssignments
),
DateAssigned AS (
    SELECT 
        n.P_ID,
        n.T_ID,
        n.TestDoctorID,
        n.N_ID,
        n.DoctorDepartment,
        fl.TestDate,

        -- AdmissionDate: TestDate + 0 or 1 days
        DATEADD(DAY, ABS(CHECKSUM(NEWID()) % 2), fl.TestDate) AS RawAdmissionDate,

        -- DischargeDate: AdmissionDate + 1 to 5 days (random)
        DATEADD(DAY, ABS(CHECKSUM(NEWID()) % 5 + 1),
            DATEADD(DAY, ABS(CHECKSUM(NEWID()) % 2), fl.TestDate)
        ) AS RawDischargeDate
    FROM Numbered n
    JOIN Fact_Labtest fl ON n.P_ID = fl.P_ID AND n.T_ID = fl.T_ID
),

-- Step 5: Clamp dates to stay in Jan 1 – Mar 31, and ≤ 7-day stay
ClampedDates AS (
    SELECT *,
        -- AdmissionDate must be ≥ Jan 1, 2025
        CASE 
            WHEN RawAdmissionDate < '2025-01-01' THEN CAST('2025-01-01' AS DATE)
            ELSE RawAdmissionDate 
        END AS AdmissionDate,

        -- DischargeDate must be ≤ Admission + 6 days and ≤ Mar 31
        CASE 
            WHEN DATEADD(DAY, 6, RawAdmissionDate) < '2025-03-31' 
                 AND RawDischargeDate <= DATEADD(DAY, 6, RawAdmissionDate) THEN RawDischargeDate
            WHEN DATEADD(DAY, 6, RawAdmissionDate) < '2025-03-31' THEN DATEADD(DAY, 6, RawAdmissionDate)
            ELSE '2025-03-31'
        END AS DischargeDate
    FROM DateAssigned
),

-- Step 6: Limit to one admission per patient
ValidAdmissions AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY P_ID ORDER BY AdmissionDate) AS rank_per_patient
    FROM ClampedDates
),
FilteredValidAdmissions AS (
    SELECT * FROM ValidAdmissions WHERE rank_per_patient = 1
),

-- Step 7: Assign rooms with max 3 patients at the same time
RoomAssignments AS (
    SELECT fva.*, r.RoomID
    FROM FilteredValidAdmissions fva
    CROSS APPLY (
        SELECT TOP 1 RoomID
        FROM Room
        WHERE Department = fva.DoctorDepartment
          AND NOT EXISTS (
              SELECT 1
              FROM Fact_Admission fa
              WHERE fa.RoomID = Room.RoomID
                AND fa.AdmissionDate < fva.DischargeDate
                AND fa.DischargeDate > fva.AdmissionDate
              GROUP BY fa.RoomID
              HAVING COUNT(*) >= 3
          )
        ORDER BY NEWID()
    ) r
)

-- Final Insert into Fact_Admission
INSERT INTO Fact_Admission (
    A_ID, P_ID, D_ID, N_ID, RoomID, AdmissionDate, DischargeDate
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY NEWID()) AS A_ID,
    P_ID,
    TestDoctorID,
    N_ID,
    RoomID,
    AdmissionDate,
    DischargeDate
FROM RoomAssignments;

-- Cleanup
DROP TABLE IF EXISTS #DoctorNursePairs;


select * from Fact_Admission
drop table Fact_Admission

-- Creating the Room table if not already present
CREATE TABLE Room (
    RoomID INT PRIMARY KEY,
    Floornumber INT,
    Roomnumber INT,
    Department VARCHAR(100)
);

BULK INSERT Room FROM 'D:\学习\Pittsburgh\capstone project\Room.csv'
WITH(firstrow = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a')

select * from Room
drop table Room

CREATE TABLE Patienthistory (
    PH_ID INT PRIMARY KEY,
    P_ID INT,
    D_ID INT,
    N_ID INT,
    Patienthistorynote VARCHAR(100),
    PatienthistoryDate DATE,
    FOREIGN KEY (P_ID) REFERENCES Patient(P_ID),
    FOREIGN KEY (D_ID) REFERENCES Doctor(D_ID),
    FOREIGN KEY (N_ID) REFERENCES Nurse(N_ID)
);

-- Step 1: Create temporary table mapping doctors and nurses by department
SELECT 
    d.D_ID,
    n.N_ID,
    d.DoctorDepartment
INTO #DoctorNursePairs
FROM Doctor d
JOIN Nurse n ON d.DoctorDepartment = n.NurseDepartment;

-- Step 2: Get doctors from Fact_Labtest (ensures only doctors who treated patients are included)
WITH DoctorPatientMatches AS (
    SELECT 
        fl.P_ID,
        fl.D_ID AS DoctorID,
        d.DoctorDepartment,
        ROW_NUMBER() OVER (PARTITION BY fl.D_ID ORDER BY NEWID()) AS DoctorPatientRank
    FROM Fact_Labtest fl
    JOIN Doctor d ON fl.D_ID = d.D_ID
),
-- Step 3: Assign a nurse from the same department
DoctorNursePatient AS (
    SELECT 
        dpm.P_ID,
        dpm.DoctorID AS D_ID,
        dnp.N_ID,
        ROW_NUMBER() OVER (PARTITION BY dnp.N_ID ORDER BY NEWID()) AS NursePatientRank
    FROM DoctorPatientMatches dpm
    JOIN #DoctorNursePairs dnp ON dpm.DoctorID = dnp.D_ID
    WHERE dpm.DoctorPatientRank <= 5  -- Limit doctor to 5 patients
)

-- Step 4: Final insert into Patienthistory
INSERT INTO Patienthistory (PH_ID, P_ID, D_ID, N_ID, Patienthistorynote, PatienthistoryDate)
SELECT 
    ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS PH_ID,
    dnp.P_ID,
    dnp.D_ID,
    dnp.N_ID,
    -- Random note
    CASE ABS(CHECKSUM(NEWID())) % 3  
        WHEN 0 THEN 'Routine Checkup'
        WHEN 1 THEN 'General Consultation'
        ELSE 'Emergency Visit'
    END,
    -- Random date between 2020 and 2023
    CONVERT(DATE, DATEADD(DAY, ABS(CHECKSUM(NEWID())) % 90, '2025-01-01'))
FROM DoctorNursePatient dnp
WHERE dnp.NursePatientRank <= 5;  -- Limit nurse to 5 patients

-- Cleanup
DROP TABLE #DoctorNursePairs;

drop table Patienthistory

select * from Patienthistory

CREATE TABLE Doctor (
    D_ID INT PRIMARY KEY,
    DoctorName VARCHAR(100),
    DoctorDepartment VARCHAR(100),
    DoctorContact VARCHAR(50)
);

BULK INSERT Doctor FROM 'D:\学习\Pittsburgh\capstone project\Doctor.csv'
WITH(firstrow = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a')

select * from Doctor
drop table Doctor

CREATE TABLE Nurse (
    N_ID INT PRIMARY KEY,
    NurseName VARCHAR(100),
    NurseDepartment VARCHAR(100),
    NurseContact VARCHAR(50)
);

BULK INSERT Nurse FROM 'D:\学习\Pittsburgh\capstone project\nurse.csv'
WITH(firstrow = 2, FIELDTERMINATOR = ',', ROWTERMINATOR = '0x0a')

select * from Nurse
