import { Chip, Empty } from './ui'

const TITLES = {
  DEVICE_REUSE_HIGH: 'Device reused across applications',
  IP_MULTI_APPLICANT: 'Many applicants from one network',
  VELOCITY_MULTI_APP_24H: 'Multiple applications in 24h',
  EMULATOR_OR_ROOTED: 'Emulator or rooted device',
  PAN_NAME_MISMATCH: 'PAN name mismatch',
  AADHAAR_PAN_NOT_LINKED: 'Aadhaar–PAN not linked',
  THIN_OR_NO_BUREAU_FILE: 'Thin / no bureau file',
  BUREAU_ENQUIRY_BURST: 'Bureau enquiry burst',
  BANK_ACCOUNT_SHARED: 'Bank account shared',
  PENNY_DROP_MISMATCH: 'Penny-drop name mismatch',
  INCOME_MISMATCH: 'Income / bank credit mismatch',
  SIM_SWAP_RECENT: 'Recent SIM swap',
  MOBILE_NAME_MISMATCH: 'Mobile owner mismatch',
  BEHAVIOUR_FAST_FORM_FILL: 'Unusually fast form fill',
  BEHAVIOUR_PASTED_FIELDS: 'Pasted identity fields',
  NOVEL_PATTERN_UNSCORED: 'Novel pattern (unscored)',
  ML_UNAVAILABLE_RULES_ONLY: 'Rules-only (ML unavailable)',
}

export default function ReasonChips({ codes }) {
  if (!codes || codes.length === 0) return <Empty>No reason codes attached.</Empty>
  return (
    <div>
      {codes.map((c) => (
        <Chip key={c} title={c}>{TITLES[c] || c}</Chip>
      ))}
    </div>
  )
}
