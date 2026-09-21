// Mock application payloads for the Apply dashboard's scenario dropdown.
// Every field is editable in the form after a scenario is picked -- this
// is what makes the demo interactive rather than a canned replay.

function base(overrides = {}) {
  const n = Math.floor(Math.random() * 999999)
  return {
    externalRef: `APP-DEMO-${n}`,
    age: 29,
    gender: 'F',
    employmentType: 'SALARIED',
    monthlyIncomeInr: 62000,
    cityTier: 2,
    pincodePrefix: '560',
    residenceType: 'RENTED',
    product: 'CONSUMER_DURABLE',
    amountInr: 85000,
    tenureMonths: 12,
    channel: 'ANDROID_APP',
    cibilScore: 712,
    isNewToCredit: false,
    activeLoans: 2,
    enquiries30d: 1,
    maxDpd12m: 0,
    creditUtilisationPct: 32.5,
    oldestAccountMonths: 58,
    panFormatValid: true,
    panNameMatchScore: 0.95,
    aadhaarPanLinked: true,
    nameDobMismatch: false,
    digilockerDocsFetched: 2,
    aadhaarLast4: '4821',
    deviceHash: `sha256:dev-${n}`,
    deviceReuseCount30d: 0,
    isEmulator: false,
    isRooted: false,
    appInstallAgeDays: 180,
    ipPrefix: '49.205',
    ipDistinctApps24h: 1,
    ipPincodeDistanceKm: 8,
    vpnOrProxy: false,
    formFillSeconds: 148,
    typingSpeedCpm: 180,
    pasteEvents: 0,
    fieldCorrections: 3,
    sessionScreens: 7,
    nightApplication: false,
    timeSincePrevAppHours: 1200,
    bankAccountHash: `sha256:bank-${n}`,
    pennyDropNameMatch: 0.97,
    accountAgeMonths: 42,
    avgMonthlyCreditInr: 60000,
    salaryCreditRegularity: 0.92,
    bounceCount6m: 0,
    accountSharedWithNApplicants: 1,
    mobileHash: `sha256:mob-${n}`,
    mobileAgeOnNetworkDays: 820,
    recentSimSwap30d: false,
    mobileNameMatch: 0.96,
    ...overrides,
  }
}

export const SCENARIOS = {
  CLEAN: {
    label: 'Clean salaried applicant',
    build: () => base(),
  },
  DEVICE_FARM: {
    label: 'Device farm (bot ring)',
    build: () =>
      base({
        deviceHash: 'sha256:devicefarm-ring-demo',
        deviceReuseCount30d: 11,
        isEmulator: true,
        isRooted: true,
        appInstallAgeDays: 0,
        formFillSeconds: 9,
        typingSpeedCpm: 850,
        pasteEvents: 4,
        fieldCorrections: 0,
        sessionScreens: 2,
        ipDistinctApps24h: 9,
        vpnOrProxy: true,
      }),
  },
  SYNTHETIC_IDENTITY: {
    label: 'Synthetic identity',
    build: () =>
      base({
        panFormatValid: false,
        panNameMatchScore: 0.22,
        aadhaarPanLinked: false,
        nameDobMismatch: true,
        isNewToCredit: true,
        cibilScore: null,
        creditUtilisationPct: null,
        oldestAccountMonths: null,
        digilockerDocsFetched: 0,
        amountInr: 150000,
      }),
  },
  MULE_ACCOUNT_RING: {
    label: 'Mule account ring',
    build: () =>
      base({
        bankAccountHash: 'sha256:mule-ring-demo',
        pennyDropNameMatch: 0.18,
        accountAgeMonths: 2,
        accountSharedWithNApplicants: 6,
        bounceCount6m: 3,
        salaryCreditRegularity: 0.15,
      }),
  },
  SIM_SWAP: {
    label: 'SIM-swap takeover',
    build: () =>
      base({
        recentSimSwap30d: true,
        mobileAgeOnNetworkDays: 2,
        mobileNameMatch: 0.24,
        appInstallAgeDays: 1,
        timeSincePrevAppHours: 0.5,
      }),
  },
  INCOME_INFLATION: {
    label: 'Income inflation',
    build: () =>
      base({
        monthlyIncomeInr: 180000,
        avgMonthlyCreditInr: 32000,
        salaryCreditRegularity: 0.2,
        bounceCount6m: 3,
        amountInr: 250000,
      }),
  },
  BOT_RING_NEW_VECTOR: {
    // Deliberately does NOT reuse the DEVICE_FARM training signature
    // (extreme device_reuse, is_emulator, sub-10s fill) -- that pattern is
    // one the supervised model already generalises to. This is a genuinely
    // different, moderate combination: risk_score=0.000 (the calibrated
    // model fully misses it), anomaly_score=0.949 (the IsolationForest
    // novelty channel screams). That gap IS the demo: a supervised model
    // trained only on known typologies would let this through; the
    // parallel unsupervised channel is what catches it. Measured directly
    // against ml-service /internal/score before wiring into the UI.
    label: '⚠ New bot ring (unseen by training)',
    build: () =>
      base({
        cibilScore: 730,
        isNewToCredit: false,
        creditUtilisationPct: 20,
        oldestAccountMonths: 60,
        maxDpd12m: 0,
        panFormatValid: true,
        panNameMatchScore: 0.9,
        aadhaarPanLinked: true,
        deviceHash: 'sha256:bot-ring-new-vector-demo',
        deviceReuseCount30d: 2,
        isEmulator: false,
        isRooted: true,
        appInstallAgeDays: 20,
        ipPrefix: '103.21',
        ipDistinctApps24h: 4,
        vpnOrProxy: true,
        formFillSeconds: 25,
        typingSpeedCpm: 380,
        pasteEvents: 3,
        fieldCorrections: 0,
        sessionScreens: 3,
        nightApplication: true,
      }),
  },
  VELOCITY_BURST: {
    label: 'Velocity burst (rapid re-apply)',
    build: () =>
      base({
        enquiries30d: 8,
        timeSincePrevAppHours: 0.2,
        ipDistinctApps24h: 3,
      }),
  },
}
