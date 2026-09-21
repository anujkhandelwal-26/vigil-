-- Policy corpus for the copilot's POLICY_LOOKUP intent (pgvector RAG).
-- Embeddings are populated by services/ml-service/app/training/embed_policy.py
-- at bootstrap time (embedding column starts NULL here).
-- Content below is an accurate practitioner summary of the named regulation,
-- not a verbatim legal reproduction, and is presented as such by the copilot.

INSERT INTO policy_chunk (source, content) VALUES
('RBI Digital Lending Directions, 2025',
 'Regulated Entities (REs) must provide the borrower a Key Fact Statement (KFS) before loan execution, disclosing the annual percentage rate, all fees, and the recovery mechanism, in a standardised, easily understood format.'),
('RBI Digital Lending Directions, 2025',
 'Borrowers are entitled to a cooling-off period during which they may exit the digital loan by paying the principal and proportionate APR, without any penalty, provided no disbursal has been utilised.'),
('RBI Digital Lending Directions, 2025',
 'Lending Service Providers (LSPs) act only as facilitators; the Regulated Entity (RE) retains full responsibility for the loan, for compliance, and for the conduct of any LSP or Digital Lending App acting on its behalf.'),
('RBI Digital Lending Directions, 2025',
 'Data collected by a Digital Lending App must be limited to what is needed for the specific loan product, collected with explicit borrower consent, and never used for any purpose beyond what was disclosed at collection.'),
('RBI Digital Lending Directions, 2025',
 'REs must maintain a public list of all LSPs and Digital Lending Apps engaged on their behalf, and disclose the recovery agent details to the borrower at the time of sanction.'),
('RBI Digital Lending Directions, 2025',
 'Automated credit limit increases without explicit borrower consent are prohibited; any change to loan terms, including limit, tenure or pricing, requires fresh, explicit borrower consent.'),

('DPDP Act, 2023',
 'Personal data may be processed only for a lawful purpose for which the Data Principal has given consent, or for a specified legitimate use; consent must be free, specific, informed, unconditional and unambiguous.'),
('DPDP Act, 2023',
 'Data Fiduciaries must practice data minimisation: personal data collected should be limited to what is necessary for the specified purpose, and retained only as long as necessary for that purpose or as required by law.'),
('DPDP Act, 2023',
 'A Data Principal has the right to access a summary of their personal data and the processing activities, the right to correction and erasure of personal data, and the right to grievance redressal.'),
('DPDP Act, 2023',
 'Consent may be withdrawn by the Data Principal at any time, with the withdrawal being as easy as giving consent; withdrawal does not affect the lawfulness of processing carried out before it.'),
('DPDP Act, 2023',
 'A Data Fiduciary must implement reasonable security safeguards to prevent personal data breach, and must notify the Data Protection Board and affected Data Principals in the event of a breach.'),
('DPDP Act, 2023',
 'Personal data processed to comply with a legal obligation, or for prevention and detection of fraud, is recognised as a certain legitimate use permitting processing without explicit prior consent, subject to notice requirements.'),

('RBI Master Direction on KYC (2016, as amended)',
 'Regulated Entities may use Video-based Customer Identification Process (V-CIP) as an alternative to physical presence, provided the process captures a live photograph, a live video, and officially valid documents with facial matching.'),
('RBI Master Direction on KYC (2016, as amended)',
 'Aadhaar-based e-KYC through offline XML or QR code verification is a permitted method of identity verification, and does not require sharing the Aadhaar number itself with the Regulated Entity.'),
('RBI Master Direction on KYC (2016, as amended)',
 'Regulated Entities must undertake Customer Due Diligence proportionate to the risk profile of the customer, with enhanced due diligence for higher-risk categories such as Politically Exposed Persons.'),
('RBI Master Direction on KYC (2016, as amended)',
 'Central KYC Registry (CKYC) records may be used to fetch previously verified KYC information for a customer, reducing duplicate document collection across Regulated Entities.'),
('RBI Master Direction on KYC (2016, as amended)',
 'A Regulated Entity must periodically update KYC records based on customer risk category, and must file a Suspicious Transaction Report (STR) with the Financial Intelligence Unit-India (FIU-IND) on detecting activity inconsistent with the customer''s known profile.'),

('Aadhaar Act, 2016, Section 29',
 'Section 29 restricts sharing of the core biometric information collected under the Aadhaar Act; the Aadhaar number itself must not be published, displayed or posted publicly, and entities are expected to store only a masked or partial reference where verification history must be retained.'),
('Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016',
 'Aadhaar-based authentication for a private entity such as a lender must rely on offline modes (XML/QR) or UIDAI-approved authentication, without the entity retaining the full Aadhaar number in its own systems beyond what is strictly necessary.'),

('CIBIL / Credit Information Companies (Regulation) Act, 2005',
 'A CIBIL score is a three-digit number typically ranging from 300 to 900, derived from a consumer''s credit history; a score of -1 or an absent score generally indicates a new-to-credit consumer with no repayment history on file.'),
('CIBIL / Credit Information Companies (Regulation) Act, 2005',
 'A sudden burst of credit enquiries across multiple lenders within a short window is a recognised indicator of application fraud or of a consumer under financial distress seeking credit from many sources simultaneously.')
;
