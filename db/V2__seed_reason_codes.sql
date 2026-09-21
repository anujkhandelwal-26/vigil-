-- Whitelisted reason codes. The LLM guardrail rejects any [CODE] token
-- output by the model that is not a key in this table.

INSERT INTO reason_code (code, title, category, customer_safe_text) VALUES
('DEVICE_REUSE_HIGH',        'Device used across many applications',      'DEVICE',    'The device used for this application has been linked to an unusually high number of recent applications.'),
('IP_MULTI_APPLICANT',       'Many applicants from one network address',  'DEVICE',    'Several applications were submitted from the same network address in a short period.'),
('VELOCITY_MULTI_APP_24H',   'Multiple applications in 24 hours',         'VELOCITY',  'More applications than usual were submitted from this profile within a single day.'),
('EMULATOR_OR_ROOTED',       'Application submitted from an emulator or rooted device', 'DEVICE', 'The application was submitted using a device configuration commonly associated with fraud.'),
('PAN_NAME_MISMATCH',        'PAN details do not match applicant name',   'KYC',       'The name on the PAN card does not sufficiently match the name provided in the application.'),
('AADHAAR_PAN_NOT_LINKED',   'Aadhaar and PAN are not linked',            'KYC',       'The Aadhaar and PAN records could not be verified as linked.'),
('THIN_OR_NO_BUREAU_FILE',   'Limited or no credit bureau history',       'BUREAU',    'There is limited credit history available to verify this application.'),
('BUREAU_ENQUIRY_BURST',     'Many recent credit enquiries',              'BUREAU',    'A high number of recent credit enquiries were found across lenders.'),
('BANK_ACCOUNT_SHARED',      'Bank account linked to multiple applicants','BANKING',   'The bank account provided is linked to more than one loan applicant.'),
('PENNY_DROP_MISMATCH',      'Bank account name verification failed',     'BANKING',   'The name on the bank account could not be sufficiently verified against the application.'),
('INCOME_MISMATCH',          'Declared income does not match bank credits','BANKING',  'The income declared does not align with amounts credited to the bank account.'),
('SIM_SWAP_RECENT',          'Recent SIM swap detected',                  'MOBILE',    'A recent change to the mobile SIM associated with this number was detected.'),
('MOBILE_NAME_MISMATCH',     'Mobile number ownership mismatch',          'MOBILE',    'The registered owner of the mobile number does not sufficiently match the applicant.'),
('BEHAVIOUR_FAST_FORM_FILL', 'Unusually fast application completion',     'BEHAVIOUR', 'The application was completed unusually quickly compared to typical applicants.'),
('BEHAVIOUR_PASTED_FIELDS',  'Key fields entered via paste, not typed',   'BEHAVIOUR', 'Key identity fields were entered by pasting rather than typing, which is unusual.'),
('NOVEL_PATTERN_UNSCORED',   'Behaviour pattern not seen in training data','MODEL',    'This application shows a behavioural pattern that differs from anything the model has seen before, and has been routed for manual review.'),
('ML_UNAVAILABLE_RULES_ONLY','Scored by rules only (ML service unavailable)', 'SYSTEM', 'This application was evaluated using baseline checks only, due to a temporary system issue.')
;
