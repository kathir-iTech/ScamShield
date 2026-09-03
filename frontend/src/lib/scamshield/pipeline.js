// ScamShield Pipeline - 1:1 JavaScript port of Python pipeline
// Requires: ./vectorizer.js and ./model.js

import * as vectorizer from './vectorizer.js';
import * as model from './model.js';
import tacticExplain from './tactic-explainers.json' with { type: 'json' };

// =============================================================================
// CONSTANTS
// =============================================================================

const SUSPICIOUS_TLDS = new Set([".xyz",".top",".club",".gq",".ml",".cf",".tk",".ga",".men",".loan",".win",".bid",".download"]);
const KNOWN_SHORTENERS = new Set(["bit.ly","tinyurl.com","tiny.cc","t.co","ow.ly","is.gd","buff.ly","shorturl.at","cutt.ly","rb.gy","bl.ink","short.link"]);

const INDIAN_BANKS = ["sbi","state bank of india","hdfc","icici","axis","kotak mahindra","pnb","punjab national bank","canara bank","bank of baroda","bob","indusind","yes bank","union bank","idbi","rbi","sebi","bandhan bank","south indian bank","federal bank","idfc first"];
const GOVERNMENT_ENTITIES = ["pm","modi","sarkari","government of india","central govt","nrega","ayushman","income tax","itr","gst","aadhaar","passport seva","epfo","esic","nsdl","csc"];
const UPI_HANDLES = new Set(["paytm","gpay","phonepe","axisbank","hdfcbank","icici","sbi","okicici","okaxis","ybl","ibl","apl","upi","fam","airtel","jio","freecharge","mobikwik"]);

const SCAM_KEYWORDS = {"upi":15,"kyc":20,"aadhaar":15,"aadhar":15,"otp":15,"deactivate":20,"blocked":15,"suspended":15,"freeze":20,"limited":10,"disconnected":20,"disconnection":20,"penalty":15,"fine":10,"lottery":25,"won":20,"cashback":15,"refund":10,"prize":20,"work from home":15,"part-time":10,"data entry":10,"registration fee":20,"customs":20,"clearance":15,"release fee":25,"illegal":20,"subsidy":15,"scheme":10,"installment":10,"pension":10,"tneb":15,"electricity":5,"bill":5,"urgent":10,"immediately":10,"expires":10,"expiring":10,"account will be":15,"click here":10,"verify now":15,"update now":10,"free":5,"guaranteed":10,"earn":10,"income":5,"processing fee":20,"registration fee":20,"exam fee":20};

const INDICATOR_PATTERNS = [
  [String.raw`\b(?:share|send|forward|whatsapp)\s+(?:this|your|the|me|it|now)\s*(?:otp|code|password)|\b(?:otp|code)\s*(?:share|send|forward)\b|one\s*time\s*password\s+(?:share|send|forward)`, "OTP Request"],
  [String.raw`\burgent\b|immediately|asap|hurry|expir(?:es|ing)\b|act now|limited time|right away`, "Urgency Language"],
  [String.raw`https?://\S+`, "Suspicious URL"],
  [String.raw`\b(?:block|suspend|freeze|deactiv|disconnect)\w*\s*(?:ed|ing)?\s+(?:within|in|after|your)`, "Account Threat"],
  [String.raw`\bpay\s+(?:now|immediately|the|this|here)\b|\btransfer\s+(?:money|funds|amount)\b|\b(?:fee|fine|penalty)\s+(?:of\s+)?(?:rs|inr|₹)\s*\d+`, "Payment Request"],
  [String.raw`\b(?:sbi|hdfc|icici|axis|kotak|pnb|bank\s+of|rbi|sebi)\b.*\b(?:block|suspend|freeze|urgent|verify|update|share|send)\b|\b(?:block|suspend|freeze|urgent|verify|update|share|send)\b.*\b(?:sbi|hdfc|icici|axis|kotak|pnb|bank\s+of|rbi|sebi)\b`, "Bank Impersonation"],
  [String.raw`\bkyc\s+(?:update|verify|expire|pending|urgent)\b|\bverify\s+(?:your\s+)?(?:account|kyc|aadhaar|pan)\b|\bupdate\s+(?:your\s+)?(?:kyc|aadhaar|pan|bank)\b`, "KYC Update Request"],
  [String.raw`\b(?:lottery|won|winner|prize|jackpot)\b.*\b(?:claim|collect|transfer|pay|fee|register)\b|\bclaim\s+(?:your\s+)?(?:prize|lottery|reward|cashback)\b`, "Prize/Lottery Mention"],
  [String.raw`\bupi\s+(?:pin|password|otp)\b|\b(?:gpay|phonepe|paytm|bhim)\s+(?:pin|password|otp)\b`, "Payment App Mention"],
  [String.raw`\bloan\s+(?:approved|guaranteed|instant|apply|register)\b|\bemi\s+(?:pay|transfer|send)\b|\bcredit\s+card\s+(?:verify|update|share)`, "Loan/EMI Mention"],
  [String.raw`\bjob\s+(?:offer|guaranteed|apply|register|fee)\b|\bwork\s+from\s+home\s+(?:guaranteed|earn|income)\b`, "Job Offer"],
  [String.raw`\binvestment\s+(?:guaranteed|return|profit|earn)\b|\bguaranteed\s+(?:return|profit|income)\b`, "Investment Offer"],
  [String.raw`\b(?:customs|clearance)\s+(?:fee|pay|charge|release)\b|\bcourier\s+(?:fee|pay|charge|stuck|held)\b`, "Courier/Customs Mention"],
  [String.raw`\belectricity\s+(?:bill|disconnect|cut|suspend)\b|\b(?:tneb|disconnection)\s+(?:notice|fee|pay)\b`, "Utility Bill Mention"],
  [String.raw`\bpm\b|\bmodi\b|\bsarkari\b|\bgovernment\s+of\b|\bcentral\s+govt\b|\bnrega\b|\bayushman\b`, "Government Impersonation"],
  [String.raw`qr\s*code|scan\s*(?:the\s*)?(?:qr\s*)?code`, "QR Code Request"],
  [String.raw`\bbitcoin|crypto|cryptocurrency|blockchain|btc\b|eth\b`, "Cryptocurrency Mention"],
  [String.raw`customer\s*(?:care|support|service)|help\s*(?:desk|line)|toll\s*free|helpline`, "Customer Care Impersonation"]
];

const HIGH_WEIGHT_KEYWORDS = new Set(["kyc","aadhaar","aadhar","upi","otp"]);
const MEDIUM_WEIGHT_KEYWORDS = new Set(["lottery","won","prize","customs","clearance"]);

const CRITICAL_INDICATORS = new Set(["OTP Request","Payment Request","Account Threat","QR Code Request"]);
const HIGH_RISK_INDICATORS = new Set(["Bank Impersonation","KYC Update Request","Investment Offer","Courier/Customs Mention"]);

const SEVERITY_CRITICAL = "CRITICAL";
const SEVERITY_HIGH = "HIGH";
const SEVERITY_MEDIUM = "MEDIUM";
const SEVERITY_LOW = "LOW";
const SEVERITY_VERY_LOW = "VERY LOW";

const RISK_HIGH = "high";
const RISK_MEDIUM = "medium";
const RISK_LOW = "low";
const ML_LABEL_SCAM = "scam";
const ML_LABEL_SAFE = "safe";
const CONFIDENCE_HIGH = "HIGH";
const CONFIDENCE_MEDIUM = "MEDIUM";
const CONFIDENCE_LOW = "LOW";

const HIGH_CONFIDENCE_THRESHOLD = 0.8;
const MEDIUM_CONFIDENCE_THRESHOLD = 0.7;

const UNKNOWN_CATEGORY = "Unknown Scam";

const CATEGORY_KEYWORDS = {
  "Bank KYC Scam": ["kyc","aadhaar","aadhar","sbi","hdfc","icici","axis","kotak","pnb","canara","bob","indusind","bank","account will be","deactivate","blocked","freeze","suspended"],
  "Lottery Scam": ["lottery","won","prize","winner","jackpot","claim","cashback","refund"],
  "Job Scam": ["work from home","part-time","data entry","registration fee","exam fee","job","salary","processing fee"],
  "UPI Scam": ["upi","gpay","phonepe","paytm","bhim","amazon pay","qr code"],
  "Investment Scam": ["investment","profit","guaranteed","return","earn","income","scheme","installment"],
  "Courier Scam": ["courier","parcel","customs","clearance","release fee","shipment","package","import"],
  "Government Scheme Scam": ["pm","modi","sarkari","government of india","central govt","subsidy","pension","nrega","ayushman"],
  "Electricity Bill Scam": ["electricity","bill","tneb","disconnection","disconnected"],
  "Customs Scam": ["customs","clearance","illegal","release fee","seized"],
  "Loan Scam": ["loan","emi","processing fee","personal loan","credit"],
  "Fake Customer Care": ["customer care","toll free","helpdesk","support","helpline","customer service"],
  "QR Code Scam": ["qr code","scan"],
  "Crypto Scam": ["bitcoin","crypto","cryptocurrency","blockchain","btc","eth"]
};

const CATEGORY_THREATS = {
  "Bank KYC Scam": {"primary":"Financial Theft","secondary":"Identity Theft"},
  "Lottery Scam": {"primary":"Financial Fraud","secondary":"Advance Fee Fraud"},
  "Job Scam": {"primary":"Employment Fraud","secondary":"Identity Theft"},
  "UPI Scam": {"primary":"Financial Theft","secondary":"Credential Harvesting"},
  "Investment Scam": {"primary":"Investment Fraud","secondary":"Ponzi Scheme"},
  "Courier Scam": {"primary":"Advance Fee Fraud","secondary":"Impersonation Fraud"},
  "Government Scheme Scam": {"primary":"Government Impersonation","secondary":"Identity Theft"},
  "Electricity Bill Scam": {"primary":"Utility Fraud","secondary":"Impersonation Fraud"},
  "Customs Scam": {"primary":"Advance Fee Fraud","secondary":"Impersonation Fraud"},
  "Loan Scam": {"primary":"Loan Fraud","secondary":"Advance Fee Fraud"},
  "Fake Customer Care": {"primary":"Technical Support Fraud","secondary":"Remote Access Scam"},
  "QR Code Scam": {"primary":"Payment Fraud","secondary":"Credential Harvesting"},
  "Crypto Scam": {"primary":"Cryptocurrency Fraud","secondary":"Investment Fraud"},
  "Unknown Scam": {"primary":"Unsolicited Message","secondary":"Social Engineering"}
};

const CATEGORY_RECOMMENDATIONS = {
  "Bank KYC Scam": ["Do not click any links claiming KYC update","Never share OTP, PIN, or password with anyone","Contact your bank directly using the official customer care number","Report to cybercrime.gov.in or forward message to 1930"],
  "Lottery Scam": ["Lotteries requiring payment to claim prizes are always fake","Do not respond to unsolicited prize notifications","Never pay advance fees to claim winnings","Block and report the sender"],
  "Job Scam": ["Legitimate employers never charge registration or exam fees","Verify the company independently before sharing personal data","Do not pay any upfront fees for job offers","Report suspicious job offers to cybercrime.gov.in"],
  "UPI Scam": ["Never share UPI PIN or scan unknown QR codes","Do not approve payment requests from unknown senders","Verify payment requests through the official app only","Report fraud to your bank and cybercrime.gov.in immediately"],
  "Investment Scam": ["Unsolicited investment offers promising high returns are scams","Verify the investment scheme with SEBI before investing","Never invest based on SMS or WhatsApp messages","Report fraudulent schemes to SEBI and cybercrime.gov.in"],
  "Courier Scam": ["Customs or courier companies never request payment via SMS","Track parcels using official courier websites only","Do not pay any release fee or customs charge through SMS links","Report courier scams to cybercrime.gov.in"],
  "Government Scheme Scam": ["Government schemes never ask for OTP or bank details via SMS","Verify scheme details on official government websites only","Do not share Aadhaar or bank account details in response to SMS","Report impersonation of government officials to cybercrime.gov.in"],
  "Electricity Bill Scam": ["Electricity boards do not threaten immediate disconnection via SMS","Verify outstanding bills on the official electricity board portal","Do not make payments through links in SMS messages","Report fraudulent disconnection threats to the local electricity office"],
  "Customs Scam": ["Customs departments do not request clearance fees via SMS","Do not pay any fees to release parcels through SMS instructions","Verify shipment status on official courier tracking portals","Report customs fraud to cybercrime.gov.in"],
  "Loan Scam": ["Legitimate lenders do not ask for advance processing fees","Verify the lender's registration with RBI before proceeding","Never share bank account or KYC details via SMS","Report illegal lending apps and SMS to cybercrime.gov.in"],
  "Fake Customer Care": ["Always use the official customer care number from the company website","Never share OTP, password, or remote access to your phone","Customer care agents never ask for UPI PIN or banking passwords","Report fake customer care numbers to the platform and cybercrime.gov.in"],
  "QR Code Scam": ["Never scan QR codes from unknown or unsolicited messages","Verify the payment screen before entering UPI PIN","QR code payments should only be used for in-person transactions","Report QR code fraud to your bank immediately"],
  "Crypto Scam": ["Unsolicited cryptocurrency investment offers are always scams","Verify any crypto scheme with SEBI or RBI before investing","Never share wallet private keys or recovery phrases","Report crypto scams to cybercrime.gov.in"],
  "Unknown Scam": ["Do not click any links in unsolicited messages","Never share OTP, passwords, or banking details via SMS","Verify the sender independently before taking any action","Report suspicious messages to cybercrime.gov.in or forward to 1930"]
};

// Evidence constants
const EVIDENCE_CORRELATIONS = {
  "credential_theft": {"label":"Credential Theft","required":["OTP Request","KYC Update Request"],"optional":["Bank Impersonation","Suspicious URL","Shortened URL","Account Threat"],"min_optional":1,"description":"Message targets banking credentials through OTP and KYC manipulation"},
  "payment_fraud": {"label":"Payment Fraud","required":["Payment Request"],"optional":["UPI ID","Shortened URL","Suspicious URL","Payment App Mention","QR Code Request"],"min_optional":1,"description":"Message directs victim to make payments through fraudulent channels"},
  "delivery_scam": {"label":"Delivery Scam","required":["Courier/Customs Mention"],"optional":["Payment Request","Suspicious URL","Urgency Language","Phone Number"],"min_optional":1,"description":"Message impersonates courier or customs to extract advance fees"},
  "phishing": {"label":"Phishing","required":["Suspicious URL"],"optional":["Government Impersonation","Bank Impersonation","KYC Update Request","Urgency Language"],"min_optional":1,"description":"Message uses a deceptive link to steal credentials or personal data"},
  "financial_scam": {"label":"Financial Scam","required":["Investment Offer"],"optional":["Cryptocurrency Mention","Urgency Language","Social Handle","Email Address"],"min_optional":1,"description":"Message promotes fraudulent investment or cryptocurrency schemes"},
  "employment_fraud": {"label":"Employment Fraud","required":["Job Offer"],"optional":["Payment Request","Email Address","Phone Number","Urgency Language"],"min_optional":1,"description":"Message offers fake employment opportunities to collect fees or data"},
  "identity_theft": {"label":"Identity Theft","required":["KYC Update Request"],"optional":["Suspicious URL","Account Threat","Government Impersonation","OTP Request"],"min_optional":1,"description":"Message attempts to collect Aadhaar, PAN or other identity documents"},
  "advance_fee_fraud": {"label":"Advance Fee Fraud","required":["Prize/Lottery Mention","Payment Request"],"optional":["Phone Number","Urgency Language","Email Address"],"min_optional":0,"description":"Message promises a prize or reward in exchange for an upfront payment"},
  "utility_fraud": {"label":"Utility Fraud","required":["Utility Bill Mention"],"optional":["Payment Request","Account Threat","Suspicious URL","Urgency Language"],"min_optional":1,"description":"Message impersonates a utility provider demanding immediate payment"},
  "tech_support_fraud": {"label":"Tech Support Fraud","required":["Customer Care Impersonation"],"optional":["Account Threat","Phone Number","Urgency Language"],"min_optional":0,"description":"Message impersonates customer support to gain remote access or credentials"}
};

const ENTITY_INDICATOR_MAP = {"bank_name":"Bank Impersonation","upi_id":"UPI ID","shortened_url":"Shortened URL","email":"Email Address","phone_indian":"Phone Number","phone_international":"Phone Number","url":"Suspicious URL","suspicious_tld":"Suspicious URL"};

const INTELLIGENCE_INDICATOR_MAP = {"shortened_url":"Shortened URL","suspicious_tld":"Suspicious TLD","otp_code":"OTP Code","upi_id":"UPI ID","email":"Email Address","bank_name":"Bank Name","currency_amount":"Currency Amount","qr_keyword":"QR Payment Request","phone_indian":"Indian Phone Number","phone_international":"International Phone Number","ifsc_code":"IFSC Code","bank_account":"Bank Account Number","ip_address":"IP Address"};

const ENTITY_RISK_MAP = {
  "shortened_url":{"risk":"HIGH","reason":"Destination hidden behind URL shortener"},
  "suspicious_tld":{"risk":"HIGH","reason":"Common phishing infrastructure"},
  "otp_code":{"risk":"HIGH","reason":"Active authentication credential"},
  "upi_id":{"risk":"MEDIUM","reason":"Direct payment request possible"},
  "email":{"risk":"MEDIUM","reason":"Potential phishing or impersonation"},
  "phone":{"risk":"MEDIUM","reason":"Potential contact for scam operations"},
  "phone_indian":{"risk":"MEDIUM","reason":"Indian telecom contact point"},
  "phone_international":{"risk":"MEDIUM","reason":"International contact point"},
  "ip_address":{"risk":"MEDIUM","reason":"Direct network identifier"},
  "ifsc_code":{"risk":"MEDIUM","reason":"Bank account targeting"},
  "bank_account":{"risk":"HIGH","reason":"Direct financial instrument"},
  "url":{"risk":"LOW","reason":"May lead to phishing site"},
  "domain":{"risk":"LOW","reason":"May host malicious content"},
  "currency_amount":{"risk":"LOW","reason":"Financial transaction mention"},
  "bank_name":{"risk":"LOW","reason":"Institutional reference"},
  "government_entity":{"risk":"LOW","reason":"Government impersonation possible"},
  "qr_keyword":{"risk":"MEDIUM","reason":"QR-based payment request"},
  "tracking_id":{"risk":"LOW","reason":"Courier reference identifier"},
  "social_handle":{"risk":"LOW","reason":"Potential social media vector"},
  "transaction_id":{"risk":"LOW","reason":"Transaction reference identifier"}
};

const EVIDENCE_TYPE_CONFLICT = "conflict";
const EVIDENCE_TYPE_CORRELATION = "correlation";
const HIGH_RISK_REASON_KEYWORDS = new Set(["otp","share","suspicious","threat","block","suspend"]);

const INDICATOR_SEVERITY_RULES = [
  ["OTP Request", SEVERITY_HIGH, 20],
  ["Account Threat", SEVERITY_HIGH, 20],
  ["Payment Request", SEVERITY_HIGH, 20],
  ["Suspicious URL", SEVERITY_HIGH, 18],
  ["Shortened URL", SEVERITY_HIGH, 18],
  ["QR Code Request", SEVERITY_HIGH, 18]
];

// Assessment constants
const ASSESSMENT_MAX_ML_POINTS = 25;
const ASSESSMENT_MAX_DECISION_POINTS = 30;
const ASSESSMENT_MAX_EVIDENCE_POINTS = 20;
const ASSESSMENT_MAX_INDICATOR_POINTS = 10;
const ASSESSMENT_MAX_ENTITY_POINTS = 10;
const ASSESSMENT_MAX_CONFLICT_PENALTY = 3;
const ASSESSMENT_EVIDENCE_HIGH_CAP = 15;
const ASSESSMENT_EVIDENCE_MED_CAP = 6;
const ASSESSMENT_EVIDENCE_HIGH_POINTS = 5;
const ASSESSMENT_EVIDENCE_MED_POINTS = 2;
const ASSESSMENT_MANUAL_REVIEW_CONFIDENCE_THRESHOLD = 0.7;
const ASSESSMENT_MAX_SCORE = 100;

const ASSESSMENT_IMMEDIATE_ACTION = "Suitable for immediate action";
const ASSESSMENT_INVESTIGATION = "Suitable for security investigation";
const ASSESSMENT_REVIEW = "Further assessment required";
const ASSESSMENT_NORMAL = "Suitable for normal communication";

// Decision constants
const DECISION_MAX_WEIGHT = 100;
const DECISION_HIGH_BONUS_THRESHOLD = 3;
const DECISION_HIGH_BONUS2_THRESHOLD = 5;
const DECISION_HIGH_BONUS = 5;
const DECISION_CONFLICT_PENALTY = 5;

const CONFIDENCE_BREAKDOWN_ML_WEIGHT = 0.25;
const CONFIDENCE_BREAKDOWN_RULES_WEIGHT = 0.30;
const CONFIDENCE_BREAKDOWN_ENTITIES_WEIGHT = 0.20;
const CONFIDENCE_BREAKDOWN_EXPLANATION_WEIGHT = 0.25;

// Intelligence extraction constants
const ENTITY_SOURCE_REGEX = "regex";
const ENTITY_SOURCE_KEYWORD = "keyword";
const ENTITY_SOURCE_INFERENCE = "inference";

const URL_PATTERNS = [String.raw`https?://(?:[-\w.]|%[\da-fA-F]{2})+(?::\d+)?(?:/[^\s]*)?`, String.raw`(?<!//)\bwww\.[-\w.]+(?:\.[a-z]{2,})(?:/[^\s]*)?`];
const PHONE_PATTERNS = [[String.raw`(?:\+91[-.\s]?|0)?[6789]\d{9}\b`, "phone_indian", 0.95], [String.raw`\+\d{1,3}[-.\s]?\d{6,14}\b`, "phone_international", 0.90], [String.raw`1[8-9]00[-.\s]?\d{3}[-.\s]?\d{4}\b`, "phone_indian", 0.90], [String.raw`0\d{2,4}[-.\s]?\d{6,8}\b`, "phone_indian", 0.85]];
const CURRENCY_PATTERNS = [String.raw`(?:rs|inr|₹)\s*[\d,]+(?:\s*(?:lakh|crore|k|thousand))?`, String.raw`\b\d[\d,]*(?:\s*(?:lakh|crore|k|thousand))?\s*(?:rs|inr|₹)`, String.raw`(?:\$|usd|eur|gbp)\s*[\d,]+(?:\.\d{2})?`];
const OTP_EXTRACT_PATTERNS = [[String.raw`\botp\s*(?::|-|is)?\s*(\d{4,8})\b`, 0.92, true], [String.raw`(?:code|pin)\s*(?::|-|is)?\s*(\d{4,8})\b`, 0.80, true], [String.raw`\b\d{4,8}\b`, 0.60, false]];
const SOCIAL_HANDLE_PATTERNS = [[String.raw`@[a-z0-9_]{3,30}\b`, "social_handle", 0.85], [String.raw`(?:t\.me|telegram)\s*(?:/|:)?\s*@?[a-z0-9_]+`, "social_handle", 0.90]];
const TRACKING_KEYWORDS = ["track","shipment","courier","parcel","tracking","order","dispatch"];
const TRACKING_PATTERNS = [[String.raw`\b[A-Z]{2}\d{9}[A-Z]{2}\b`, "tracking_id", 0.95], [String.raw`\b1Z[A-Z0-9]{14,18}\b`, "tracking_id", 0.95], [String.raw`\b\d{12,16}\b`, "tracking_id", 0.55]];
const TRANSACTION_KEYWORDS = ["txn","transaction","ref","reference","payment id","utr","rrn"];
const TRANSACTION_PATTERNS = [[String.raw`\b(?:txn|trn|ref)[:\s]*[a-z0-9]{8,20}\b`, 0.90], [String.raw`\b\d{12}\b`, 0.60]];

const EVIDENCE_MAX_HIGH_ENTITIES = 6;
const EVIDENCE_MAX_MEDIUM_ENTITIES = 6;

// =============================================================================
// HELPERS
// =============================================================================

function reEscape(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildRe(pattern, flags) {
  return new RegExp(pattern, flags || '');
}

function matchWord(text, word) {
  const pat = buildRe(String.raw`\b` + reEscape(word) + String.raw`\b`, 'i');
  return pat.test(text);
}

function matchPhrase(text, phrase) {
  if (phrase.includes(' ')) {
    return text.includes(phrase);
  }
  return matchWord(text, phrase);
}

// =============================================================================
// RULES ENGINE
// =============================================================================

function _has_scam_context(t) {
  const urgency = ["urgent","immediately","asap","right away","hurry","limited time","expires","expiring","final notice","last warning"];
  const threats = ["block","suspend","freeze","deactivate","disconnect","cancel","legal","police","arrest","case filed"];
  const requests = ["click here","call now","reply","confirm","verify","share","send","forward","whatsapp"];
  for (const w of urgency) { if (matchWord(t, w)) return true; }
  for (const w of threats) { if (matchWord(t, w)) return true; }
  for (const w of requests) { if (matchWord(t, w)) return true; }
  return false;
}

const RULE_WEIGHTS = {
  "otp_request": 5.0, "otp_share_request": 20.0, "urgency_word": 5.0,
  "money_mention": 8.0, "suspension_threat": 15.0, "url_shortener": 15.0,
  "suspicious_tld": 15.0, "url_suspicious_keywords": 10.0, "url_present": 5.0,
  "multiple_urls": 5.0, "bank_mention": 3.0, "payment_app_mention": 3.0,
  "scam_keyword": 2.0, "govt_reference": 5.0
};
const THRESHOLDS = {"high": 70.0, "medium": 35.0, "low": 0.0};

function check_otp(text) {
  const t = text.toLowerCase();
  let score = 0;
  const reasons = [];
  const otp_patterns = [String.raw`\botp\b`, String.raw`one[\s-]*time[\s-]*password`, String.raw`verification code`, String.raw`(?:otp|code)\s*[:\-]\s*\d{4,8}`];
  for (const p of otp_patterns) {
    if (buildRe(p).test(t)) {
      const sharing_ref = (buildRe(String.raw`\bshare\b`).test(t) && !buildRe(String.raw`\bdo\s+not\s+share\b`).test(t)) || (buildRe(String.raw`\bsend\b`).test(t) && !buildRe(String.raw`\bdo\s+not\s+send\b`).test(t));
      if (sharing_ref || t.includes("forward") || t.includes("whatsapp")) {
        score += RULE_WEIGHTS["otp_share_request"];
        reasons.push("Message asks you to share OTP with someone");
      } else if (_has_scam_context(t)) {
        score += RULE_WEIGHTS["otp_request"];
        reasons.push("Contains OTP-sensitive keywords with suspicious context");
      }
      break;
    }
  }
  return { score, reasons };
}

function check_urgent_money(text) {
  const t = text.toLowerCase();
  let score = 0;
  const reasons = [];

  const urgency_words = ["urgent","immediately","asap","right away","now","hurry","limited time","expires","expiring","today only","final notice","last warning"];
  for (const w of urgency_words) {
    if (matchWord(t, w)) {
      score += RULE_WEIGHTS["urgency_word"];
      reasons.push("Urgency keyword: '" + w + "'");
      break;
    }
  }

  const money_phrases_demand = [
    [String.raw`pay(?:\s*now|\s*immediately|\s*the)`, "Payment demand detected"],
    [String.raw`transfer\s*(?:money|funds|amount)`, "Money transfer request"],
    [String.raw`(?:fee|fine|penalty|payment)\s*(?:of\s*)?(?:rs|inr|₹)?\s*[\d,]+`, "Specific monetary demand"]
  ];
  for (const [pat, reason] of money_phrases_demand) {
    if (buildRe(pat).test(t)) {
      score += RULE_WEIGHTS["money_mention"];
      reasons.push(reason);
      break;
    }
  }

  const money_mention_only = [
    [String.raw`(?:rs|inr|₹)\s*[\d,]+`, "Mentions a monetary amount"],
    [String.raw`credit\s*(?:card|score|limit)`, "Credit-related mention"],
    [String.raw`(?:loan|emi)`, "Loan or EMI mentioned"]
  ];
  for (const [pat, reason] of money_mention_only) {
    if (buildRe(pat).test(t)) {
      if (_has_scam_context(t)) {
        score += RULE_WEIGHTS["money_mention"];
        reasons.push(reason);
      }
      break;
    }
  }

  if (buildRe(String.raw`(?:block|suspend|freeze|deactiv|disconnect|cancel)\s*(?:ed|ing)?\s*(?:within|in|after)`).test(t)) {
    score += RULE_WEIGHTS["suspension_threat"];
    reasons.push("Threat of account suspension/disconnection");
  }

  return { score, reasons };
}

function check_suspicious_links(text) {
  let score = 0;
  const reasons = [];
  const urls = text.match(/https?:\/\/(?:[-\w.]|%[\da-fA-F]{2})+[^\s]*/g) || [];

  for (const url of urls) {
    let domain = '';
    try {
      const u = new URL(url.includes('://') ? url : 'http://' + url);
      domain = u.hostname.toLowerCase();
    } catch(e) {
      domain = '';
    }

    let shortenerFound = false;
    for (const s of KNOWN_SHORTENERS) {
      if (domain.includes(s)) {
        score += RULE_WEIGHTS["url_shortener"];
        reasons.push("Use of URL shortener: " + domain);
        shortenerFound = true;
        break;
      }
    }
    if (shortenerFound) continue;

    let suspiciousTld = false;
    for (const tld of SUSPICIOUS_TLDS) {
      if (domain.endsWith(tld)) {
        score += RULE_WEIGHTS["suspicious_tld"];
        reasons.push("Suspicious TLD in URL: " + tld);
        suspiciousTld = true;
        break;
      }
    }
    if (suspiciousTld) continue;

    const suspicious_keywords_in_url = ["kyc","update","verify","secure","login","account","bank","upi","aadhaar","aadhar","otp","confirm","reset"];
    let hasSuspicious = false;
    for (const kw of suspicious_keywords_in_url) {
      if (domain.includes(kw)) {
        score += RULE_WEIGHTS["url_suspicious_keywords"];
        reasons.push("URL contains suspicious keywords: " + domain);
        hasSuspicious = true;
        break;
      }
    }
    if (hasSuspicious) continue;

    const known_legit_domains = new Set(["flipkart.com","amazon.in","amazon.com","flipkart.co.in","paytm.com","phonepe.com","whatsapp.com","google.com","facebook.com","youtube.com","instagram.com","twitter.com","linkedin.com","outlook.com","hotmail.com","gmail.com","yahoo.com","reddit.com","netflix.com","amazon.co.in"]);
    if (!known_legit_domains.has(domain)) {
      score += RULE_WEIGHTS["url_present"];
      reasons.push("Contains a URL link");
    }
  }

  if (urls.length > 1) {
    score += RULE_WEIGHTS["multiple_urls"];
    reasons.push("Multiple URLs in message");
  }

  return { score, reasons };
}

function check_service_keywords(text) {
  const t = text.toLowerCase();
  let score = 0;
  const reasons = [];

  const india_banks = ["sbi","hdfc","icici","axis","kotak","pnb","canara","bob","indusind","rbi","sebi"];
  for (const bank of india_banks) {
    if (matchWord(t, bank)) {
      if (_has_scam_context(t)) {
        score += RULE_WEIGHTS["bank_mention"];
        reasons.push("Bank/financial institution mentioned: '" + bank + "'");
      }
      break;
    }
  }
  if (matchWord(t, "yes bank") || matchWord(t, "union bank")) {
    if (_has_scam_context(t)) {
      score += RULE_WEIGHTS["bank_mention"];
      reasons.push("Bank/financial institution mentioned");
    }
  }

  const payment_apps = ["gpay","phonepe","paytm","bhim","upi","amazon pay"];
  for (const app of payment_apps) {
    if (matchWord(t, app)) {
      if (_has_scam_context(t)) {
        score += RULE_WEIGHTS["payment_app_mention"];
        reasons.push("Payment app mentioned: '" + app + "'");
      }
      break;
    }
  }

  const matched = [];
  for (const [kw, pts] of Object.entries(SCAM_KEYWORDS)) {
    const pattern = kw.includes(' ') ? reEscape(kw) : String.raw`\b` + reEscape(kw) + String.raw`\b`;
    if (buildRe(pattern).test(t)) {
      if (_has_scam_context(t)) {
        score += pts * RULE_WEIGHTS["scam_keyword"];
        matched.push(kw);
      }
    }
  }
  if (matched.length > 0) {
    reasons.push("Suspicious keywords: " + matched.slice(0,3).join(", "));
  }

  const govt_refs = ["pm","modi","sarkari","government of india","central govt","nrega","ayushman"];
  for (const ref of govt_refs) {
    if (matchPhrase(t, ref)) {
      if (_has_scam_context(t)) {
        score += RULE_WEIGHTS["govt_reference"];
        reasons.push("Government scheme reference: '" + ref + "'");
      }
      break;
    }
  }

  return { score, reasons };
}

function analyze_message(text) {
  let score = 0;
  const all_reasons = [];

  const check_fns = [check_otp, check_urgent_money, check_suspicious_links, check_service_keywords];
  for (const fn of check_fns) {
    const { score: s, reasons } = fn(text);
    score += s;
    all_reasons.push(...reasons);
  }

  score = Math.min(score, 100.0);

  let risk;
  if (score >= THRESHOLDS["high"]) risk = "high";
  else if (score >= THRESHOLDS["medium"]) risk = "medium";
  else risk = "low";

  return { risk_score: Math.round(score * 10) / 10, risk_label: risk, reasons: all_reasons.slice(0, 5) };
}

// =============================================================================
// ENTITY EXTRACTION
// =============================================================================

function extract_urls(text) {
  const found = [];
  const seen = new Set();
  for (const pat of URL_PATTERNS) {
    const re = buildRe(pat, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      let raw = m[0].replace(/[.,;:!?)]+$/, '');
      if (raw.endsWith(')')) raw = raw.slice(0, -1);
      if (!seen.has(raw)) {
        seen.add(raw);
        const entity = { value: raw, type: "url", confidence: 0.99, source: ENTITY_SOURCE_REGEX };
        try {
          const u = new URL(raw.includes('://') ? raw : 'http://' + raw);
          const domain = u.hostname.toLowerCase();
          let shortener = false;
          for (const s of KNOWN_SHORTENERS) {
            if (domain.includes(s)) { entity.type = "shortened_url"; shortener = true; break; }
          }
          if (!shortener) {
            for (const tld of SUSPICIOUS_TLDS) {
              if (domain.endsWith(tld)) { entity.type = "suspicious_tld"; break; }
            }
          }
        } catch(e) {}
        found.push(entity);
      }
    }
  }
  return found;
}

function extract_domains(text) {
  const found = [];
  const seen = new Set();
  const re = buildRe(String.raw`\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b`, 'gi');
  let m;
  while ((m = re.exec(text)) !== null) {
    const raw = m[0].toLowerCase();
    if (!seen.has(raw)) {
      seen.add(raw);
      if (!text.includes('https://' + raw) && !text.includes('http://' + raw)) {
        found.push({ value: raw, type: "domain", confidence: 0.95, source: ENTITY_SOURCE_REGEX });
      }
    }
  }
  return found;
}

function extract_emails(text) {
  const found = [];
  const seen = new Set();
  const re = buildRe(String.raw`\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b`, 'gi');
  let m;
  while ((m = re.exec(text)) !== null) {
    const raw = m[0].toLowerCase();
    if (!seen.has(raw)) { seen.add(raw); found.push({ value: raw, type: "email", confidence: 0.98, source: ENTITY_SOURCE_REGEX }); }
  }
  return found;
}

function extract_phones(text) {
  const found = [];
  const seen = new Set();
  for (const [p, ptype, conf] of PHONE_PATTERNS) {
    const re = buildRe(p, 'g');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0].replace(/[.,;:!?)]+$/g, '');
      if (!seen.has(raw)) { seen.add(raw); found.push({ value: raw, type: ptype, confidence: conf, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function extract_upi_ids(text) {
  const found = [];
  const seen = new Set();
  const re = buildRe(String.raw`\b[a-z0-9._-]+@[a-z]{3,}\b`, 'gi');
  let m;
  while ((m = re.exec(text)) !== null) {
    const raw = m[0].toLowerCase();
    const parts = raw.split('@');
    const handle = parts.length > 1 ? parts[1] : '';
    if (UPI_HANDLES.has(handle)) {
      if (!seen.has(raw)) { seen.add(raw); found.push({ value: raw, type: "upi_id", confidence: 0.97, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function extract_qr_keywords(text) {
  const found = [];
  const re = buildRe(String.raw`\bqr\s*code\b|\bscan\s*(?:the\s*)?(?:qr\s*)?code\b`, 'gi');
  let m;
  while ((m = re.exec(text)) !== null) {
    found.push({ value: m[0], type: "qr_keyword", confidence: 0.95, source: ENTITY_SOURCE_REGEX });
  }
  return found;
}

function extract_bank_names(text) {
  const found = [];
  const seen = new Set();
  const t = text.toLowerCase();
  for (const bank of INDIAN_BANKS) {
    const pattern = bank.includes(' ') ? reEscape(bank) : String.raw`\b` + reEscape(bank) + String.raw`\b`;
    if (buildRe(pattern, 'i').test(t)) {
      if (!seen.has(bank)) { seen.add(bank); found.push({ value: bank.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '), type: "bank_name", confidence: 0.90, source: ENTITY_SOURCE_KEYWORD }); }
    }
  }
  return found;
}

function extract_government_entities(text) {
  const found = [];
  const seen = new Set();
  const t = text.toLowerCase();
  for (const entity of GOVERNMENT_ENTITIES) {
    const pattern = entity.includes(' ') ? reEscape(entity) : String.raw`\b` + reEscape(entity) + String.raw`\b`;
    if (buildRe(pattern, 'i').test(t)) {
      if (!seen.has(entity)) { seen.add(entity); found.push({ value: entity.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '), type: "government_entity", confidence: 0.85, source: ENTITY_SOURCE_KEYWORD }); }
    }
  }
  return found;
}

function extract_currency_amounts(text) {
  const found = [];
  const seen = new Set();
  for (const pat of CURRENCY_PATTERNS) {
    const re = buildRe(pat, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0].trim().toLowerCase();
      if (!seen.has(raw)) { seen.add(raw); found.push({ value: m[0], type: "currency_amount", confidence: 0.88, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function extract_otp_codes(text) {
  const found = [];
  const seen = new Set();
  if (!buildRe(String.raw`\botp\b`, 'i').test(text)) return found;
  for (const [p, conf, hasGroup] of OTP_EXTRACT_PATTERNS) {
    if (found.length > 0) break;
    const re = buildRe(p, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0];
      if (!seen.has(raw)) {
        seen.add(raw);
        const val = (hasGroup && m[1]) ? m[1] : raw;
        found.push({ value: val.trim(), type: "otp_code", confidence: conf, source: ENTITY_SOURCE_REGEX });
      }
    }
  }
  if (found.length === 0) {
    const numericRe = buildRe(String.raw`\b\d{4,8}\b`);
    const codes = text.match(numericRe);
    if (codes && codes.length > 0) {
      found.push({ value: codes[0], type: "otp_code", confidence: 0.70, source: ENTITY_SOURCE_INFERENCE });
    }
  }
  return found;
}

function extract_shortened_urls(text) {
  const found = [];
  const seen = new Set();
  for (const shortener of KNOWN_SHORTENERS) {
    const re = buildRe(String.raw`https?://` + reEscape(shortener) + String.raw`/\S+`, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0].replace(/[.,;:!?)]+$/, '');
      if (!seen.has(raw)) { seen.add(raw); found.push({ value: raw, type: "shortened_url", confidence: 0.99, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function extract_suspicious_tlds(text) {
  const found = [];
  const seen = new Set();
  for (const tld of SUSPICIOUS_TLDS) {
    const re = buildRe(String.raw`https?://(?:[-\w.]+?)` + reEscape(tld) + String.raw`(?:/[^\s]*)?`, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const domain = m[0];
      if (!seen.has(domain)) { seen.add(domain); found.push({ value: domain, type: "suspicious_tld", confidence: 0.95, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function extract_ip_addresses(text) {
  const found = [];
  const seen = new Set();
  const ipv4re = buildRe(String.raw`\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b`, 'g');
  const ipv6re = buildRe(String.raw`\b(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}\b`, 'g');
  let m;
  while ((m = ipv4re.exec(text)) !== null) {
    if (!seen.has(m[0])) { seen.add(m[0]); found.push({ value: m[0], type: "ip_address", confidence: 0.99, source: ENTITY_SOURCE_REGEX }); }
  }
  while ((m = ipv6re.exec(text)) !== null) {
    if (!seen.has(m[0])) { seen.add(m[0]); found.push({ value: m[0], type: "ip_address", confidence: 0.98, source: ENTITY_SOURCE_REGEX }); }
  }
  return found;
}

function extract_social_handles(text) {
  const found = [];
  const seen = new Set();
  for (const [p, etype, conf] of SOCIAL_HANDLE_PATTERNS) {
    const re = buildRe(p, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0];
      const pos = m.index;
      const key = raw.toLowerCase();
      if (seen.has(key)) continue;
      if (pos > 0 && /[a-z0-9]/i.test(text[pos - 1])) continue;
      const atParts = raw.split('@');
      if (atParts.length === 2 && UPI_HANDLES.has(atParts[1].toLowerCase())) continue;
      seen.add(key);
      found.push({ value: raw, type: etype, confidence: conf, source: ENTITY_SOURCE_REGEX });
    }
  }
  return found;
}

function extract_ifsc_codes(text) {
  const found = [];
  const seen = new Set();
  const re = buildRe(String.raw`\b[A-Z]{4}0[A-Z0-9]{6}\b`, 'g');
  let m;
  while ((m = re.exec(text)) !== null) {
    if (!seen.has(m[0])) { seen.add(m[0]); found.push({ value: m[0], type: "ifsc_code", confidence: 0.99, source: ENTITY_SOURCE_REGEX }); }
  }
  return found;
}

function extract_bank_accounts(text) {
  const found = [];
  const seen = new Set();
  const re = buildRe(String.raw`\b\d{9,18}\b`, 'g');
  let m;
  while ((m = re.exec(text)) !== null) {
    const raw = m[0];
    if (!seen.has(raw)) {
      seen.add(raw);
      if (/^\d{4,8}$/.test(raw)) continue;
      if (/^[6789]\d{9}$/.test(raw)) continue;
      found.push({ value: raw, type: "bank_account", confidence: 0.55, source: ENTITY_SOURCE_REGEX });
    }
  }
  return found;
}

function extract_tracking_ids(text) {
  const found = [];
  const seen = new Set();
  const t = text.toUpperCase();
  const hasKeyword = TRACKING_KEYWORDS.some(kw => t.toLowerCase().includes(kw));
  for (const [p, etype, conf] of TRACKING_PATTERNS) {
    const re = buildRe(p, 'g');
    let m;
    while ((m = re.exec(t)) !== null) {
      const raw = m[0];
      const cleaned = raw.replace(/\s+/g, '');
      if (!seen.has(cleaned) && hasKeyword) {
        seen.add(cleaned);
        found.push({ value: cleaned, type: etype, confidence: conf, source: ENTITY_SOURCE_REGEX });
      }
    }
  }
  return found;
}

function extract_transaction_ids(text) {
  const found = [];
  const seen = new Set();
  const hasKeyword = TRANSACTION_KEYWORDS.some(kw => text.toLowerCase().includes(kw));
  for (const [p, conf] of TRANSACTION_PATTERNS) {
    const re = buildRe(p, 'gi');
    let m;
    while ((m = re.exec(text)) !== null) {
      const raw = m[0];
      if (!seen.has(raw) && hasKeyword) { seen.add(raw); found.push({ value: raw, type: "transaction_id", confidence: conf, source: ENTITY_SOURCE_REGEX }); }
    }
  }
  return found;
}

function intelligence_analyze(text) {
  const all_entities = [];
  all_entities.push(...extract_urls(text));
  all_entities.push(...extract_domains(text));
  all_entities.push(...extract_emails(text));
  all_entities.push(...extract_phones(text));
  all_entities.push(...extract_upi_ids(text));
  all_entities.push(...extract_qr_keywords(text));
  all_entities.push(...extract_bank_names(text));
  all_entities.push(...extract_government_entities(text));
  all_entities.push(...extract_currency_amounts(text));
  all_entities.push(...extract_otp_codes(text));
  all_entities.push(...extract_ip_addresses(text));
  all_entities.push(...extract_social_handles(text));
  all_entities.push(...extract_ifsc_codes(text));
  all_entities.push(...extract_bank_accounts(text));
  all_entities.push(...extract_tracking_ids(text));
  all_entities.push(...extract_transaction_ids(text));

  const seen_values = new Set();
  const deduped = [];
  for (const e of all_entities) {
    const key = e.value.toLowerCase() + '|' + e.type;
    if (!seen_values.has(key)) {
      seen_values.add(key);
      if (!e.risk) {
        const riskInfo = ENTITY_RISK_MAP[e.type] || { risk: "LOW" };
        e.risk = riskInfo.risk;
        e.risk_reason = riskInfo.reason || "Unknown entity type";
      }
      deduped.push(e);
    }
  }

  const by_type = {};
  const threat_indicators = [];
  const risk_entities = {};

  for (const e of deduped) {
    const etype = e.type;
    by_type[etype] = (by_type[etype] || 0) + 1;
    const risk = e.risk || "LOW";
    const riskKey = risk.toLowerCase();
    if (!risk_entities[riskKey]) risk_entities[riskKey] = [];
    risk_entities[riskKey].push(e);
  }

  for (const e of deduped) {
    const label = INTELLIGENCE_INDICATOR_MAP[e.type];
    if (label && !threat_indicators.includes(label) && (e.risk === "HIGH" || e.risk === "MEDIUM")) {
      threat_indicators.push(label);
    }
  }

  return {
    entities: deduped,
    entity_summary: { total_entities: deduped.length, by_type, threat_indicators },
    entity_risk: { high: risk_entities["high"] || [], medium: risk_entities["medium"] || [], low: risk_entities["low"] || [] }
  };
}

// =============================================================================
// EXPLANATION
// =============================================================================

const _INDICATOR_REGEXES = INDICATOR_PATTERNS.map(([p, label]) => [buildRe(p, 'i'), label]);

function _weight_for_keyword(kw) {
  if (HIGH_WEIGHT_KEYWORDS.has(kw)) return 3;
  if (MEDIUM_WEIGHT_KEYWORDS.has(kw)) return 2;
  return 1;
}

const _CATEGORY_REGEXES = {};
for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
  const entries = [];
  for (const kw of keywords) {
    const pat = kw.includes(' ') ? reEscape(kw) : String.raw`\b` + reEscape(kw) + String.raw`\b`;
    entries.push([kw, buildRe(pat, 'i'), _weight_for_keyword(kw)]);
  }
  _CATEGORY_REGEXES[cat] = entries;
}

function detect_category(text, reasons) {
  const text_lower = text.toLowerCase();
  const weighted_scores = {};

  for (const [cat, entries] of Object.entries(_CATEGORY_REGEXES)) {
    let score = 0;
    for (const [kw, pat, weight] of entries) {
      const matches = text_lower.match(new RegExp(pat.source, 'gi'));
      if (matches) score += matches.length * weight;
    }
    if (score > 0) weighted_scores[cat] = score;
  }

  for (const reason of reasons) {
    const r_lower = reason.toLowerCase();
    for (const [cat, entries] of Object.entries(_CATEGORY_REGEXES)) {
      for (const [kw, pat, weight] of entries) {
        if (pat.test(r_lower)) {
          weighted_scores[cat] = (weighted_scores[cat] || 0) + 2;
        }
      }
    }
  }

  if (Object.keys(weighted_scores).length === 0) return { category: UNKNOWN_CATEGORY, certainty: 0.0 };

  let best_cat = UNKNOWN_CATEGORY;
  let best_score = 0;
  for (const [cat, s] of Object.entries(weighted_scores)) {
    if (s > best_score) { best_score = s; best_cat = cat; }
  }
  const total = Object.values(weighted_scores).reduce((a, b) => a + b, 0);
  const certainty = total > 0 ? Math.round(best_score / total * 100) / 100 : 0.0;
  return { category: best_cat, certainty };
}

function detect_indicators(text, reasons) {
  const seen = new Set();
  const indicators = [];
  const text_lower = text.toLowerCase();
  for (const [pattern, label] of _INDICATOR_REGEXES) {
    if (!seen.has(label) && pattern.test(text_lower)) {
      indicators.push(label);
      seen.add(label);
    }
  }
  for (const reason of reasons) {
    const r_lower = reason.toLowerCase();
    for (const [pattern, label] of _INDICATOR_REGEXES) {
      if (!seen.has(label) && pattern.test(r_lower)) {
        indicators.push(label);
        seen.add(label);
      }
    }
  }
  return indicators;
}

function calculate_severity(ml_label, confidence, rule_score, rule_label, indicators) {
  const has_critical = indicators.some(i => CRITICAL_INDICATORS.has(i));
  const indicator_count = indicators.length;
  const has_high_risk = indicators.some(i => HIGH_RISK_INDICATORS.has(i));

  if (rule_label === RISK_HIGH && has_critical) return SEVERITY_CRITICAL;
  if (ml_label === ML_LABEL_SCAM && rule_score >= 35 && has_critical) return SEVERITY_CRITICAL;
  if (rule_label === RISK_HIGH) return SEVERITY_HIGH;
  if (ml_label === ML_LABEL_SCAM && confidence > 0.9) return SEVERITY_HIGH;
  if (ml_label === ML_LABEL_SCAM && rule_score >= 20) return SEVERITY_HIGH;
  if (has_critical && (ml_label === ML_LABEL_SCAM || indicator_count >= 2)) return SEVERITY_HIGH;

  if (ml_label === ML_LABEL_SCAM && confidence > MEDIUM_CONFIDENCE_THRESHOLD && (rule_score >= 10 || indicator_count >= 1 || has_high_risk)) return SEVERITY_MEDIUM;
  if (ml_label === ML_LABEL_SCAM && confidence > MEDIUM_CONFIDENCE_THRESHOLD && indicator_count === 0 && rule_score < 10 && !has_high_risk && !has_critical) return SEVERITY_LOW;

  if (rule_score >= 20) return SEVERITY_MEDIUM;
  if (has_critical) return SEVERITY_MEDIUM;
  if (indicator_count >= 2) return SEVERITY_MEDIUM;
  if (has_high_risk) return SEVERITY_MEDIUM;
  if (rule_score > 0) return SEVERITY_LOW;
  return SEVERITY_VERY_LOW;
}

function build_summary(category, severity, ml_label, rule_label, indicators) {
  if (ml_label === ML_LABEL_SCAM && rule_label === RISK_HIGH) {
    return "Highly suspicious " + category.toLowerCase() + " detected. Both ML and rule engine independently confirm scam indicators.";
  }
  if (ml_label === ML_LABEL_SCAM) {
    return "Suspicious message potentially related to " + category.toLowerCase() + ". ML classifier detects scam patterns.";
  }
  if (rule_label === RISK_HIGH) {
    return "Message flagged with high-risk indicators related to " + category.toLowerCase() + ". Rule engine detects strong scam signals.";
  }
  if (rule_label === RISK_MEDIUM) {
    return "Message shows moderate risk indicators potentially related to " + category.toLowerCase() + ". Exercise caution before responding.";
  }
  if (indicators.length > 0) {
    return "Message contains some suspicious elements but no confirmed scam classification. Detected: " + indicators.slice(0,3).join(", ") + ".";
  }
  return "Message appears safe with no significant scam indicators.";
}

function generate_explanation(text, analysis_result) {
  const prediction = analysis_result.prediction || ML_LABEL_SAFE;
  const confidence = analysis_result.confidence || 0.0;
  const rule_score = analysis_result.rule_score || 0.0;
  const rule_label = analysis_result.rule_label || RISK_LOW;
  const reasons = analysis_result.reasons || [];

  const { category, certainty } = detect_category(text, reasons);
  const indicators = detect_indicators(text, reasons);
  const severity = calculate_severity(prediction, confidence, rule_score, rule_label, indicators);
  const threats = CATEGORY_THREATS[category] || CATEGORY_THREATS[UNKNOWN_CATEGORY];
  const recommendations = CATEGORY_RECOMMENDATIONS[category] || CATEGORY_RECOMMENDATIONS[UNKNOWN_CATEGORY];
  const summary = build_summary(category, severity, prediction, rule_label, indicators);

  let confidence_reason;
  if (prediction === ML_LABEL_SCAM && confidence > HIGH_CONFIDENCE_THRESHOLD) {
    confidence_reason = "High confidence because both ML and rule engine independently classified the message as suspicious.";
  } else if (prediction === ML_LABEL_SCAM) {
    confidence_reason = "Moderate confidence based on ML classification and detected scam indicators.";
  } else if (rule_score >= 35) {
    confidence_reason = "Low ML confidence but rule engine detected several suspicious indicators.";
  } else {
    confidence_reason = "No significant scam indicators detected across ML and rule analysis.";
  }

  return {
    summary,
    risk_level: severity,
    scam_category: category,
    confidence_reason,
    detected_indicators: indicators,
    threats: [threats.primary, threats.secondary],
    recommended_actions: recommendations
  };
}

// =============================================================================
// EVIDENCE
// =============================================================================

let _evId = 0;
function _evReset() { _evId = 0; }
function _evAdd(items, etype, source, desc, severity, conf, weight) {
  _evId++;
  items.push({ id: 'ev_' + String(_evId).padStart(3, '0'), type: etype, source, description: desc, severity, confidence: Math.round(conf * 100) / 100, weight });
}

const _SEV_MAP = { [RISK_HIGH]: SEVERITY_HIGH, [RISK_MEDIUM]: SEVERITY_MEDIUM, [RISK_LOW]: SEVERITY_LOW };

const RISK_TYPES = ["credential_theft", "financial_loss", "identity_theft", "malware", "social_engineering"];

// Faithful JS port of backend/domains/assessment/evidence.py _INDICATOR_RISK_RULES
const _INDICATOR_RISK_RULES = [
  ["OTP Request", { credential_theft: 30, identity_theft: 20 }, []],
  ["Bank Impersonation", { credential_theft: 25, financial_loss: 15 }, []],
  ["Payment Request", { financial_loss: 35 }, []],
  ["Suspicious URL", { social_engineering: 25 }, []],
  ["Shortened URL", { social_engineering: 20 }, ["shortened_url"]],
  ["Prize/Lottery Mention", { financial_loss: 25, social_engineering: 15 }, []],
  ["Investment Offer", { financial_loss: 30 }, []],
  ["Job Offer", { financial_loss: 20, identity_theft: 15 }, []],
  ["Government Impersonation", { identity_theft: 25, social_engineering: 15 }, []],
  ["KYC Update Request", { identity_theft: 30, credential_theft: 20 }, []],
  ["Account Threat", { social_engineering: 20 }, []],
  ["Cryptocurrency Mention", { financial_loss: 25 }, []],
  ["QR Code Request", { financial_loss: 20 }, []],
  ["Customer Care Impersonation", { social_engineering: 20, credential_theft: 15 }, []],
  ["Courier/Customs Mention", { financial_loss: 25, social_engineering: 10 }, []],
  ["Utility Bill Mention", { financial_loss: 20, social_engineering: 15 }, []],
  ["Loan/EMI Mention", { financial_loss: 20, identity_theft: 10 }, []]
];

const _ENTITY_RISK_RULES = [
  [["UPI ID", "upi_id"], { financial_loss: 30, credential_theft: 15 }],
  [["email"], { social_engineering: 15 }],
  [["phone_indian", "phone_international"], { social_engineering: 15 }]
];

const _CORRELATION_RISK_RULES = [
  ["Credential Theft", { credential_theft: 20 }],
  ["Payment Fraud", { financial_loss: 20 }],
  ["Phishing", { social_engineering: 15, credential_theft: 15 }],
  ["Financial Scam", { financial_loss: 20 }]
];

function correlate_evidence(indicators, entities) {
  const found = [];
  const entity_types = new Set(entities.map(e => e.type));
  const indicator_set = new Set(indicators);
  const seen = new Set();

  for (const [key, corr] of Object.entries(EVIDENCE_CORRELATIONS)) {
    const required = new Set(corr.required);
    const has_required = required.size === 0 || [...required].every(r => indicator_set.has(r));
    if (!has_required) continue;
    const optional_matches = corr.optional.filter(o => indicator_set.has(o));
    const optional_from_entities = [];
    for (const [etype, indicator_label] of Object.entries(ENTITY_INDICATOR_MAP)) {
      if (entity_types.has(etype)) optional_from_entities.push(indicator_label);
    }
    const all_optional = new Set([...optional_matches, ...optional_from_entities]);
    if (all_optional.size >= corr.min_optional) {
      if (!seen.has(corr.label)) {
        seen.add(corr.label);
        found.push({ type: EVIDENCE_TYPE_CORRELATION, label: corr.label, description: corr.description });
      }
    }
  }
  return found;
}

function build_risk_breakdown(indicators, entities, category, correlations) {
  const risks = {};
  for (const k of RISK_TYPES) risks[k] = 0;
  const indicator_set = new Set(indicators);
  const entity_types = new Set(entities.map(e => e.type));
  const corr_labels = new Set(correlations.map(c => c.label));

  for (const [indicator, risk_map, entity_types_needed] of _INDICATOR_RISK_RULES) {
    if (indicator_set.has(indicator) || (entity_types_needed && entity_types_needed.some(et => entity_types.has(et)))) {
      for (const [key, value] of Object.entries(risk_map)) risks[key] += value;
    }
  }

  for (const [entity_types_required, risk_map] of _ENTITY_RISK_RULES) {
    if (entity_types_required.some(et => entity_types.has(et))) {
      for (const [key, value] of Object.entries(risk_map)) risks[key] += value;
    }
  }

  for (const [corr_label, risk_map] of _CORRELATION_RISK_RULES) {
    if (corr_labels.has(corr_label)) {
      for (const [key, value] of Object.entries(risk_map)) risks[key] += value;
    }
  }

  for (const k of RISK_TYPES) risks[k] = Math.min(risks[k], 100);
  return risks;
}

function detect_conflicts(prediction, confidence, rule_label, rule_score, indicators, entities) {
  const conflicts = [];
  const high_risk_entities = entities.filter(e => e.risk === "HIGH");

  if (prediction === ML_LABEL_SAFE && rule_label === RISK_HIGH) {
    conflicts.push({ type: "ml_vs_rules", description: "ML classifies as safe but rule engine reports high risk. Rule engine detected strong scam signals that the ML model may have missed." });
  }
  if (prediction === ML_LABEL_SAFE && high_risk_entities.length > 0) {
    conflicts.push({ type: "ml_vs_entities", description: "ML classifies as safe but " + high_risk_entities.length + " high-risk indicator(s) were extracted from the message." });
  }
  if (prediction === ML_LABEL_SAFE && confidence > 0.9 && rule_label === RISK_MEDIUM) {
    conflicts.push({ type: "high_confidence_safe_with_risk", description: "ML is highly confident the message is safe, but rule engine detected moderate risk signals." });
  }
  if (prediction === ML_LABEL_SCAM && rule_label === RISK_LOW && confidence < 0.7) {
    conflicts.push({ type: "ml_vs_rules_low_conf", description: "ML classifies as scam with low confidence while rule engine found no significant indicators." });
  }
  if (prediction === ML_LABEL_SCAM && confidence > 0.9 && indicators.length === 0 && high_risk_entities.length === 0) {
    conflicts.push({ type: "ml_high_conf_no_evidence", description: "ML is highly confident this is a scam but no concrete indicators or entities were detected." });
  }
  return conflicts;
}

function calculate_decision_score(evidence_list) {
  if (evidence_list.length === 0) return 0;
  const total_weight = evidence_list.reduce((s, e) => s + e.weight, 0);
  const raw = Math.min(total_weight, DECISION_MAX_WEIGHT);
  let bonus = 0;
  const high_count = evidence_list.filter(e => e.severity === SEVERITY_HIGH).length;
  if (high_count >= DECISION_HIGH_BONUS_THRESHOLD) bonus += DECISION_HIGH_BONUS;
  if (high_count >= DECISION_HIGH_BONUS2_THRESHOLD) bonus += DECISION_HIGH_BONUS;
  const conflict_count = evidence_list.filter(e => e.type === EVIDENCE_TYPE_CONFLICT).length;
  if (conflict_count > 0) bonus = Math.max(bonus - DECISION_CONFLICT_PENALTY, 0);
  return Math.min(raw + bonus, 100);
}

function build_confidence_breakdown(prediction, confidence, rule_label, rule_score, indicators, entities) {
  const ml_score = Math.round(confidence * 100);
  let rules_score;
  if (rule_label === RISK_HIGH) rules_score = 85;
  else if (rule_label === RISK_MEDIUM) rules_score = 55;
  else rules_score = 15;

  const entity_count = entities.length;
  let entities_score;
  if (entity_count >= 4) entities_score = 80;
  else if (entity_count >= 2) entities_score = 55;
  else if (entity_count >= 1) entities_score = 30;
  else entities_score = 10;

  const indicator_count = indicators.length;
  let explanation_score;
  if (indicator_count >= 4) explanation_score = 85;
  else if (indicator_count >= 2) explanation_score = 60;
  else if (indicator_count >= 1) explanation_score = 35;
  else explanation_score = 10;

  const overall = Math.round(ml_score * CONFIDENCE_BREAKDOWN_ML_WEIGHT + rules_score * CONFIDENCE_BREAKDOWN_RULES_WEIGHT + entities_score * CONFIDENCE_BREAKDOWN_ENTITIES_WEIGHT + explanation_score * CONFIDENCE_BREAKDOWN_EXPLANATION_WEIGHT);
  return { ml: ml_score, rules: rules_score, entities: entities_score, explanation: explanation_score, overall };
}

function build_evidence(analysis) {
  const prediction = analysis.prediction || ML_LABEL_SAFE;
  const confidence = analysis.confidence || 0.0;
  const rule_score = analysis.rule_score || 0.0;
  const rule_label = analysis.rule_label || RISK_LOW;
  const reasons = analysis.reasons || [];
  const indicators = analysis.detected_indicators || [];
  const category = analysis.scam_category || UNKNOWN_CATEGORY;
  const entities = analysis.entities || [];
  const entity_summary = analysis.entity_summary || {};
  const entity_risk = analysis.entity_risk || {};

  _evReset();
  const items = [];

  _evAdd(items, "ml_prediction", "ml",
    "ML model classifies message as '" + prediction + "' with " + Math.round(confidence * 100) + "% confidence",
    prediction === ML_LABEL_SCAM ? SEVERITY_HIGH : SEVERITY_LOW,
    confidence,
    prediction === ML_LABEL_SCAM ? 20 : 0
  );

  _evAdd(items, "rule_score", "rules",
    "Rule engine score: " + rule_score + "/100 (" + rule_label + " risk)",
    _SEV_MAP[rule_label] || SEVERITY_LOW,
    Math.min(rule_score / 100 + 0.2, 0.99),
    Math.min(Math.round(rule_score * 0.3), 25)
  );

  for (const reason of reasons) {
    const desc_lower = reason.toLowerCase();
    let sev = SEVERITY_MEDIUM;
    let w = 10;
    let hasHighRiskReason = false;
    for (const kw of HIGH_RISK_REASON_KEYWORDS) {
      if (desc_lower.includes(kw)) { hasHighRiskReason = true; break; }
    }
    if (hasHighRiskReason) { sev = SEVERITY_HIGH; w = 18; }
    _evAdd(items, "rule_indicator", "rules", reason, sev, 0.80, w);
  }

  const indicator_set = new Set(indicators);
  for (const indicator of indicators) {
    let sev = SEVERITY_MEDIUM;
    let w = 12;
    for (const [name, high_sev, high_w] of INDICATOR_SEVERITY_RULES) {
      if (indicator === name) { sev = high_sev; w = high_w; break; }
    }
    _evAdd(items, "indicator", "explanation", "Detected: " + indicator, sev, 0.85, w);
  }

  const high_entities = entity_risk.high || [];
  const medium_entities = entity_risk.medium || [];

  for (const ent of high_entities.slice(0, EVIDENCE_MAX_HIGH_ENTITIES)) {
    _evAdd(items, "entity_high", "intel", "High-risk entity: " + ent.type + " (" + ent.value + ")", SEVERITY_HIGH, 0.90, 22);
  }
  for (const ent of medium_entities.slice(0, EVIDENCE_MAX_MEDIUM_ENTITIES)) {
    _evAdd(items, "entity_medium", "intel", "Medium-risk entity: " + ent.type + " (" + ent.value + ")", SEVERITY_MEDIUM, 0.80, 14);
  }

  const total_entities = entity_summary.total_entities || 0;
  if (total_entities >= 3) {
    _evAdd(items, "entity_volume", "intel", "Multiple entities detected: " + total_entities + " total", SEVERITY_MEDIUM, 0.75, 12);
  }

  const threat_indicators = entity_summary.threat_indicators || [];
  for (const ti of threat_indicators) {
    _evAdd(items, "threat_indicator", "intel", "Threat indicator: " + ti, SEVERITY_HIGH, 0.85, 16);
  }

  const correlations = correlate_evidence(indicators, entities);
  for (const corr of correlations) {
    _evAdd(items, "correlation", "evidence", corr.description, SEVERITY_HIGH, 0.88, 22);
  }

  const conflicts = detect_conflicts(prediction, confidence, rule_label, rule_score, indicators, entities);
  for (const conflict of conflicts) {
    _evAdd(items, "conflict", "evidence", conflict.description, SEVERITY_MEDIUM, 0.70, 10);
  }

  const decision_score = calculate_decision_score(items);
  const confidence_breakdown = build_confidence_breakdown(prediction, confidence, rule_label, rule_score, indicators, entities);
  const risk_breakdown = build_risk_breakdown(indicators, entities, category, correlations);

  const supporting = items.filter(e => (e.severity === SEVERITY_HIGH || e.severity === SEVERITY_MEDIUM) && e.type !== EVIDENCE_TYPE_CONFLICT);
  const conflicting = items.filter(e => e.type === EVIDENCE_TYPE_CONFLICT);

  return {
    decision_score,
    supporting_evidence: supporting.slice(0, 8),
    conflicting_evidence: conflicting,
    confidence_breakdown,
    risk_breakdown
  };
}

// =============================================================================
// ASSESSMENT
// =============================================================================

function assess(analysis) {
  const prediction = analysis.prediction || ML_LABEL_SAFE;
  const confidence = analysis.confidence || 0.0;
  const decision_score = analysis.decision_score || 0;
  const rule_label = analysis.rule_label || "low";
  const rule_score = analysis.rule_score || 0;
  const indicators = analysis.detected_indicators || [];
  const category = analysis.scam_category || UNKNOWN_CATEGORY;
  const entity_risk = analysis.entity_risk || {};
  const supporting_evidence = analysis.supporting_evidence || [];
  const conflicting_evidence = analysis.conflicting_evidence || [];
  const evidence_conf_breakdown = analysis.confidence_breakdown || {};

  let ml_points;
  if (prediction === ML_LABEL_SCAM) {
    ml_points = Math.round(ASSESSMENT_MAX_ML_POINTS * confidence);
  } else {
    ml_points = Math.round(ASSESSMENT_MAX_ML_POINTS * (1 - confidence));
  }
  ml_points = Math.min(ml_points, ASSESSMENT_MAX_ML_POINTS);

  if (prediction === ML_LABEL_SCAM && confidence < MEDIUM_CONFIDENCE_THRESHOLD) {
    if (indicators.length === 0 && rule_label === RISK_LOW && !(entity_risk.high && entity_risk.high.length > 0)) {
      ml_points = Math.round(ml_points * 0.3);
    }
  }

  const decision_points = Math.round(ASSESSMENT_MAX_DECISION_POINTS * (decision_score / 100));

  const high_count = supporting_evidence.filter(e => e.severity === "HIGH").length;
  const med_count = supporting_evidence.filter(e => e.severity === "MEDIUM").length;
  let evidence_points = Math.min(high_count * ASSESSMENT_EVIDENCE_HIGH_POINTS, ASSESSMENT_EVIDENCE_HIGH_CAP) + Math.min(med_count * ASSESSMENT_EVIDENCE_MED_POINTS, ASSESSMENT_EVIDENCE_MED_CAP);
  evidence_points = Math.min(evidence_points, ASSESSMENT_MAX_EVIDENCE_POINTS);

  const indicator_count = indicators.length;
  let indicator_points;
  if (indicator_count >= 4) indicator_points = ASSESSMENT_MAX_INDICATOR_POINTS;
  else if (indicator_count === 3) indicator_points = 9;
  else if (indicator_count === 2) indicator_points = 7;
  else if (indicator_count === 1) indicator_points = 4;
  else indicator_points = 0;

  const high_entities = entity_risk.high || [];
  const med_entities = entity_risk.medium || [];
  let entity_points = Math.min(high_entities.length * 3, 6) + Math.min(med_entities.length * 2, 4);
  entity_points = Math.min(entity_points, ASSESSMENT_MAX_ENTITY_POINTS);

  const conflict_count = conflicting_evidence.length;
  const conflict_penalty = Math.min(conflict_count * 3, ASSESSMENT_MAX_CONFLICT_PENALTY);

  let assessment_score = ml_points + decision_points + evidence_points + indicator_points + entity_points - conflict_penalty;
  assessment_score = Math.max(0, Math.min(assessment_score, ASSESSMENT_MAX_SCORE));

  let assessment_band;
  if (assessment_score >= 76) assessment_band = ASSESSMENT_IMMEDIATE_ACTION;
  else if (assessment_score >= 51) assessment_band = ASSESSMENT_INVESTIGATION;
  else if (assessment_score >= 21) assessment_band = ASSESSMENT_REVIEW;
  else assessment_band = ASSESSMENT_NORMAL;

  const overall_conf = evidence_conf_breakdown.overall || 50;
  const has_conflict = conflict_count > 0;

  let assessment_confidence;
  if (confidence > HIGH_CONFIDENCE_THRESHOLD && overall_conf >= 60 && !has_conflict) {
    assessment_confidence = CONFIDENCE_HIGH;
  } else if (confidence > MEDIUM_CONFIDENCE_THRESHOLD || overall_conf >= 40) {
    assessment_confidence = CONFIDENCE_MEDIUM;
  } else {
    assessment_confidence = CONFIDENCE_LOW;
  }

  let review_required = false;
  let manual_review_reason = "";

  if (has_conflict && confidence > ASSESSMENT_MANUAL_REVIEW_CONFIDENCE_THRESHOLD) {
    review_required = true;
    manual_review_reason = "High ML confidence but conflicting evidence from rules or entity analysis.";
  } else if (category === UNKNOWN_CATEGORY && assessment_score >= 21) {
    review_required = true;
    manual_review_reason = "Message flagged but could not be categorized into a known scam type.";
  } else if (assessment_confidence === CONFIDENCE_LOW && assessment_score >= 21) {
    review_required = true;
    manual_review_reason = "Low assessment confidence despite elevated risk score.";
  } else if (prediction === ML_LABEL_SCAM && rule_label === RISK_LOW && confidence < MEDIUM_CONFIDENCE_THRESHOLD) {
    review_required = true;
    manual_review_reason = "ML classification lacks confidence and rule engine found no corroborating evidence.";
  }

  return { assessment_score, assessment_band, assessment_confidence, review_required, manual_review_reason };
}

// =============================================================================
// REFINEMENT
// =============================================================================

const _KNOWN_BANKS = ["sbi","state bank of india","hdfc","icici","axis","kotak","pnb","canara","bob","indusind","yes bank","idbi","bank of baroda","union bank","central bank"];
const _GOVT_ENTITIES = ["government","sarkari","pm","modi","nrega","ayushman","epfo","itr","income tax","nps","aadhaar","uidai","voter id","epic","upsc","delhi university"];
const _TRACKING_WORDS = ["tracking","track","shipment","delivery","order","dispatch","shipped","out for delivery","pickup","courier","transit","awb","delivered"];
const _TRANSACTION_WORDS = ["txn","transaction","credited","debited","received","paid","refund","payment of","trf","sent to","paid to","reward points","balance","deposit","withdrawal","interest"];
const _LEGITIMATE_BANK_PHRASES = ["your a/c","your account","has been credited","has been debited","transaction","trf","ref no","available balance","reward points","credit card payment","interest of","balance as of","monthly contribution","cash deposit","credit","debited","neft","imps","rtgs","thank you for using"];

function _has_suspicious_url(analysis) {
  const entities = analysis.entities || [];
  const known_legit = new Set(["flipkart.com","amazon.in","amazon.com","flipkart.co.in","paytm.com","phonepe.com","gpay.com","rb.gy","tinyurl.com","bit.ly","tiny.cc","shorturl.at","cutt.ly","bl.ink","whatsapp.com","telegram.me","t.me","youtube.com","google.com","facebook.com","twitter.com","instagram.com","linkedin.com","outlook.com","hotmail.com","gmail.com","yahoo.com","reddit.com","netflix.com","amazon.co.in","myntra.com","nykaa.com","ajio.com","meesho.com","airtel.in","jio.com","vi.in","bsnl.co.in","eci.gov.in","upsc.gov.in","uidai.gov.in","vit.ac.in","vit-placement.in","delhivery.com","shiprocket.in","ecom-express.com","tatapower.com","ndmc.gov.in","bsesdelhi.com"]);
  for (const e of entities) {
    const etype = e.type || "";
    if (etype !== "url" && etype !== "shortened_url" && etype !== "suspicious_tld") continue;
    const value = (e.value || "").toLowerCase();
    let domain = '';
    try {
      const u = new URL(value.includes('://') ? value : 'http://' + value);
      domain = u.hostname.toLowerCase();
    } catch(ex) { domain = ''; }
    if (known_legit.has(domain)) continue;
    return true;
  }
  const indicators = analysis.detected_indicators || [];
  for (const i of indicators) {
    const il = i.toLowerCase();
    if (il.includes("url") || il.includes("shortened") || il.includes("suspicious")) return true;
  }
  const reasons = analysis.reasons || [];
  for (const r of reasons) {
    const rl = r.toLowerCase();
    if (rl.includes("url") && (rl.includes("shorten") || rl.includes("suspicious"))) return true;
  }
  return false;
}

function _has_account_threat(analysis) { return (analysis.detected_indicators || []).includes("Account Threat"); }
function _has_payment_request(analysis) { return (analysis.detected_indicators || []).includes("Payment Request"); }
function _has_urgency(analysis) { return (analysis.detected_indicators || []).includes("Urgency Language"); }

function _text_lower(analysis) { return (analysis._original_text || "").toLowerCase(); }

function _any_keyword_in_text(analysis, keywords) {
  const t = _text_lower(analysis);
  for (const kw of keywords) { if (matchWord(t, kw)) return true; }
  return false;
}
function _entity_count(analysis) { return (analysis.entities || []).length; }
function _indicator_count(analysis) { return (analysis.detected_indicators || []).length; }

// FP Rules
function _fp_legitimate_banking_notification(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_bank_ref = _KNOWN_BANKS.some(b => matchWord(text, b));
  if (!has_bank_ref) return false;
  const has_legit_phrase = _LEGITIMATE_BANK_PHRASES.some(p => text.includes(p));
  if (!has_legit_phrase) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  return true;
}

function _fp_government_alert(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_govt = _GOVT_ENTITIES.some(g => matchWord(text, g));
  if (!has_govt) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  if (_indicator_count(analysis) >= 3) return false;
  return true;
}

function _fp_delivery_notification(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_tracking = _TRACKING_WORDS.some(t => matchWord(text, t));
  if (!has_tracking) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

function _fp_legitimate_otp(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  if (!buildRe(String.raw`\b\d{4,8}\b`).test(text)) return false;
  if (!buildRe(String.raw`\botp\b`).test(text)) return false;
  if (_has_suspicious_url(analysis)) return false;
  const negated = ["do not share","dont share","don't share","never share","do not disclose","do not send","dont send","don't send"];
  const has_negated_sharing = negated.some(n => text.includes(n));
  const has_demand_sharing = buildRe(String.raw`(?:share|send|forward|whatsapp)\s+(?:this|now|the|your|me|it)`).test(text) || buildRe(String.raw`(?:please|now)\s+(?:share|send|forward)`).test(text);
  if (has_negated_sharing) return true;
  if (has_demand_sharing) return false;
  if (buildRe(String.raw`\bshare\b`).test(text) || buildRe(String.raw`\bsend\b`).test(text)) return false;
  return true;
}

function _fp_transaction_receipt(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_transaction_word = _TRANSACTION_WORDS.some(t => matchWord(text, t));
  if (!has_transaction_word) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

function _fp_low_indicator_high_confidence(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  if ((analysis.confidence || 0) < 0.6) return false;
  if (_indicator_count(analysis) > 1) return false;
  if (_entity_count(analysis) > 0) return false;
  if ((analysis.rule_score || 0) >= 35) return false;
  return true;
}

function _fp_security_notification(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const security_phrases = ["password was changed","password has been changed","password changed successfully","security code","login alert","new device","sign-in attempt","unusual sign","unusual login","account recovery"];
  const has_security = security_phrases.some(p => text.includes(p));
  if (!has_security) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

function _fp_legitimate_marketing(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const marketing_phrases = ["free consultation","financial advisor","credit card","pre-selected","feedback matters","complete survey","rate your experience","have a great day","thank you for being a valued customer","terms apply","reply yes","opt out","unsubscribe"];
  const has_marketing = marketing_phrases.some(p => text.includes(p));
  if (!has_marketing) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_indicator_count(analysis) >= 3) return false;
  return true;
}

function _fp_subscription_reminder(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const sub_keywords = ["subscription","renewal","renew","auto-pay","auto debit","auto debit","bill due"];
  const has_sub = sub_keywords.some(k => matchWord(text, k));
  if (!has_sub) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  return true;
}

const _UPI_APPS = ["gpay","google pay","phonepe","phone pe","paytm","bhim","amazon pay","mobiwik","freecharge"];
const _ECOMMERCE_PLATFORMS = ["amazon","flipkart","myntra","nykaa","ajio","meesho","snapdeal","jabong","limeroad"];
const _DELIVERY_SERVICES = ["delhivery","ecom express","blue dart","dt dc","professional courier","india post","speed post","shiprocket","fedex","dhl","aramex"];
const _UTILITY_KEYWORDS = ["electricity","water bill","gas bill","broadband","mobile bill","postpaid","prepaid","recharge"];
const _TELECOM_ENTITIES = ["airtel","jio","vi","vodafone","bsnl","tata play","dth","jiofiber","airtel fiber","act fiber","bsnl fiber"];
const _COLLEGE_ENTITIES = ["vit","iit","nit","bits","iiit","nits","manipal","srm","amity","lpu","christ","st xaviers"];

function _fp_upi_transaction(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_upi_app = _UPI_APPS.some(a => matchWord(text, a));
  const has_upi_ref = buildRe(String.raw`upi\s*(?:ref|refno|ref no|reference)`).test(text);
  const has_transaction = ["sent to","paid to","received from","refund","successful"].some(t => text.includes(t));
  if (!has_upi_app && !has_upi_ref) return false;
  if (!has_transaction) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

function _fp_shopping_update(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_platform = _ECOMMERCE_PLATFORMS.some(p => matchWord(text, p));
  if (!has_platform) return false;
  const update_keywords = ["order","shipped","delivered","return","refund","pickup","dispatch","tracking"];
  const has_update = update_keywords.some(k => matchWord(text, k));
  if (!has_update) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

function _fp_utility_bill(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_utility = _UTILITY_KEYWORDS.some(k => matchWord(text, k));
  if (!has_utility) return false;
  if (!buildRe(String.raw`rs\.?\s*\d+|inr\s*\d+|₹\s*\d+`).test(text)) return false;
  const has_due = ["due date","due by","pay before","pay by","last date"].some(d => matchWord(text, d));
  if (!has_due) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  return true;
}

function _fp_telecom_notification(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_telecom = _TELECOM_ENTITIES.some(e => matchWord(text, e));
  if (!has_telecom) return false;
  const info_phrases = ["recharge","plan","data","expiry","expire","renew","valid","activated","monthly","speed","gb","mbps"];
  const has_info = info_phrases.some(p => text.includes(p));
  if (!has_info) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  if (_has_account_threat(analysis)) return false;
  return true;
}

function _fp_college_notification(analysis) {
  if (analysis.prediction !== ML_LABEL_SCAM) return false;
  const text = _text_lower(analysis);
  const has_college = _COLLEGE_ENTITIES.some(e => matchWord(text, e));
  if (!has_college) return false;
  const info_phrases = ["placement","exam","result","semester","attendance","assignment","lecture","lab","register","drive","campus"];
  const has_info = info_phrases.some(p => text.includes(p));
  if (!has_info) return false;
  if (_has_suspicious_url(analysis)) return false;
  if (_has_payment_request(analysis)) return false;
  return true;
}

// FN Rules
function _fn_obfuscated_url(analysis) {
  const text = _text_lower(analysis);
  const obfuscated_patterns = [String.raw`bit\s*\[?\s*dot\s*\]?\s*ly`, String.raw`hxxp[s]?://`, String.raw`h(?!ttp)[tT][tT][pP]`, String.raw`click\s*(?:here|the\s*link|this)`, String.raw`\[link\]`, String.raw`remove\s*(?:the\s*)?dots?`];
  return obfuscated_patterns.some(p => buildRe(p).test(text));
}

function _fn_unicode_spoofing(analysis) {
  const text = analysis._original_text || "";
  if (!text) return false;
  let non_ascii_count = 0;
  for (let i = 0; i < text.length; i++) { if (text.charCodeAt(i) > 127) non_ascii_count++; }
  if (non_ascii_count > 0 && non_ascii_count < text.length * 0.3) {
    if (buildRe(String.raw`https?://`, 'i').test(text)) return true;
    if (buildRe(String.raw`[\w\u0080-\uffff]+\.[\w\u0080-\uffff]+`).test(text)) return true;
  }
  return false;
}

function _fn_urgency_with_payment(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  if (!_has_urgency(analysis)) return false;
  if (!_has_payment_request(analysis)) return false;
  return true;
}

function _fn_credential_harvesting(analysis) {
  const text = _text_lower(analysis);
  const harvest_phrases = [String.raw`share\s*(?:your\s*)?(?:otp|password|pin|aadhaar|bank)`, String.raw`update\s*(?:your\s*)?(?:aadhaar|pan|bank|account)`, String.raw`verify\s*(?:your\s*)?(?:identity|account|details|kyc|pan)`, String.raw`confirm\s*(?:your\s*)?(?:details|account|information)`, String.raw`(?:login|sign.?in)\s*(?:to\s*)?(?:verify|update|confirm)`];
  return harvest_phrases.some(p => buildRe(p).test(text));
}

function _fn_social_engineering(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  const text = _text_lower(analysis);
  const has_threat = ["block","suspend","freeze","deactivate","legal","police","arrest"].some(t => text.includes(t));
  const has_reward = ["won","prize","cashback","reward","free","gift","offer"].some(r => text.includes(r));
  const has_call_to_action = ["click","call","apply","register","submit","respond"].some(c => text.includes(c));
  return [has_threat, has_reward, has_call_to_action].filter(Boolean).length >= 2;
}

function _fn_fake_support(analysis) {
  const text = _text_lower(analysis);
  const support_phrases = ["customer care","customer support","helpdesk","helpline","toll free","help line"];
  const has_support = support_phrases.some(p => text.includes(p));
  if (!has_support) return false;
  return buildRe(String.raw`\b\d{10,15}\b`).test(text) || buildRe(String.raw`1[8-9]00`).test(text);
}

function _fn_qr_payment_scam(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  if (!(analysis.detected_indicators || []).includes("QR Code Request")) return false;
  return _has_payment_request(analysis);
}

function _fn_investment_scam(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  const text = _text_lower(analysis);
  const invest_keywords = ["investment","profit","returns","return","earn","income","trading","crypto","bitcoin"];
  const has_invest = invest_keywords.some(k => buildRe(String.raw`\b` + reEscape(k)).test(text));
  if (!has_invest) return false;
  const guarantee_keywords = ["guaranteed","100%","assured","risk free","double","limited","hurry"];
  return guarantee_keywords.some(g => text.includes(g));
}

function _fn_obfuscated_contact(analysis) {
  const text = _text_lower(analysis);
  const obfuscation = [String.raw`\w+\s*\(?\s*@\s*\)?\s*\w+`, String.raw`\w+\s*\(?\s*\[?\s*\bat\b\s*\]?\s*\)?\s*\w+`, String.raw`\w+\s*\(?\s*\[?\s*\bdot\b\s*\]?\s*\)?\s*\w+`];
  return obfuscation.some(p => buildRe(p).test(text));
}

function _fn_digital_arrest_scam(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  const text = _text_lower(analysis);
  const authority_keywords = ["enforcement directorate","supreme court","high court","ncb","cbi","police","crime branch","cyber crime","anti corruption","edar","ed notice"];
  const has_authority = authority_keywords.some(k => text.includes(k));
  if (!has_authority) return false;
  const threat_keywords = ["arrest","custody","warrant","case registered","investigation","summon","attached","frozen","blackmailed","legal action"];
  return threat_keywords.some(k => text.includes(k));
}

function _fn_romance_scam(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  const text = _text_lower(analysis);
  const affection_phrases = ["fell in love","i love you","my love","dear","baby","darling","sweetheart","hi dear"];
  const has_affection = affection_phrases.some(p => text.includes(p));
  if (!has_affection) return false;
  const money_keywords = ["send","need","visa","flight","fee","transfer","money","rupees","dollars","inheritance","release fee"];
  return money_keywords.some(k => text.includes(k));
}

function _fn_job_scam(analysis) {
  if (analysis.prediction !== ML_LABEL_SAFE) return false;
  const text = _text_lower(analysis);
  const job_phrases = ["job","salary","hiring","vacancy","position","work from home","earn money","part time"];
  const has_job = job_phrases.some(p => buildRe(String.raw`\b` + reEscape(p)).test(text));
  if (!has_job) return false;
  const fee_keywords = ["training fee","training bond","registration fee","security deposit","processing fee","registration rs"];
  return fee_keywords.some(k => text.includes(k));
}

const FP_RULES = [
  { rule_id: "FP-001", description: "Legitimate banking notification misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_legitimate_banking_notification, reason: "Contains legitimate banking notification patterns (transaction/credit info with bank name, no phishing indicators). Downgrading scam confidence." },
  { rule_id: "FP-002", description: "Government alert misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_government_alert, reason: "Contains government scheme references without payment request or suspicious URLs. Likely a legitimate government communication." },
  { rule_id: "FP-003", description: "Delivery notification misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_delivery_notification, reason: "Contains delivery tracking language without payment demands or suspicious links. Likely a legitimate delivery notification." },
  { rule_id: "FP-004", description: "Legitimate OTP message misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_legitimate_otp, reason: "Contains an OTP code but no sharing request or phishing indicators. Likely a legitimate one-time password message." },
  { rule_id: "FP-005", description: "Transaction receipt misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_transaction_receipt, reason: "Contains transaction reference without payment demands or suspicious URLs. Likely a legitimate financial receipt." },
  { rule_id: "FP-006", description: "Subscription reminder misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_subscription_reminder, reason: "Contains subscription or billing reminder without account threats or phishing links. Likely a legitimate reminder." },
  { rule_id: "FP-007", description: "High ML confidence but insufficient evidence", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.15, condition: _fp_low_indicator_high_confidence, reason: "ML model is confident but lacks corroborating indicators or entities. Reducing confidence to prevent over-reliance on single signal." },
  { rule_id: "FP-008", description: "Security notification misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_security_notification, reason: "Contains security notification language (password change, login alert) without phishing indicators. Likely a legitimate security alert." },
  { rule_id: "FP-009", description: "Marketing or promotional message misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_legitimate_marketing, reason: "Contains marketing/promotional language without suspicious URLs or strong scam indicators. Likely a legitimate commercial message." },
  { rule_id: "FP-010", description: "UPI transaction confirmation misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_upi_transaction, reason: "Contains UPI transaction confirmation with reference number. Likely a legitimate payment receipt." },
  { rule_id: "FP-011", description: "Shopping/ecommerce update misclassified as scam", category: "fp_reduction", priority: "HIGH", confidence_impact: -0.25, condition: _fp_shopping_update, reason: "Contains order update or return confirmation from known ecommerce platform. Likely a legitimate order notification." },
  { rule_id: "FP-012", description: "Utility bill notification misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_utility_bill, reason: "Contains utility bill notification with amount and due date. Likely a legitimate bill reminder." },
  { rule_id: "FP-013", description: "Telecom notification misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_telecom_notification, reason: "Contains telecom provider name with plan/recharge info. Likely a legitimate telecom notification." },
  { rule_id: "FP-014", description: "College notification misclassified as scam", category: "fp_reduction", priority: "MEDIUM", confidence_impact: -0.20, condition: _fp_college_notification, reason: "Contains college name with academic info. Likely a legitimate college notification." }
];

const FN_RULES = [
  { rule_id: "FN-001", description: "Obfuscated URL not detected", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.25, condition: _fn_obfuscated_url, reason: "Message contains obfuscated URL patterns indicating attempt to evade detection. Increasing scam confidence." },
  { rule_id: "FN-002", description: "Unicode spoofing in URL or domain", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_unicode_spoofing, reason: "Message uses Unicode characters for domain spoofing, a common phishing technique. Increasing scam confidence." },
  { rule_id: "FN-003", description: "Urgency combined with payment request", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_urgency_with_payment, reason: "Message combines urgency language with direct payment demands, a hallmark of financial scams. Increasing scam confidence." },
  { rule_id: "FN-004", description: "Credential harvesting attempt", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.25, condition: _fn_credential_harvesting, reason: "Message explicitly requests sensitive credentials (OTP, password, Aadhaar, bank details). Strong indicator of credential harvesting. Increasing scam confidence." },
  { rule_id: "FN-005", description: "Social engineering pattern detected", category: "fn_reduction", priority: "MEDIUM", confidence_impact: 0.15, condition: _fn_social_engineering, reason: "Message combines threat, reward, and call-to-action — classic social engineering triad. Increasing scam confidence." },
  { rule_id: "FN-006", description: "Fake customer support detected", category: "fn_reduction", priority: "MEDIUM", confidence_impact: 0.15, condition: _fn_fake_support, reason: "Message impersonates customer support with contact details, a common technique for credential harvesting. Increasing scam confidence." },
  { rule_id: "FN-007", description: "QR code payment scam", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_qr_payment_scam, reason: "Message combines QR code request with payment demand, indicating a QR-based payment scam. Increasing scam confidence." },
  { rule_id: "FN-008", description: "Investment scam with guaranteed returns", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_investment_scam, reason: "Message offers investment with guaranteed returns and urgency, typical of Ponzi schemes. Increasing scam confidence." },
  { rule_id: "FN-009", description: "Obfuscated contact information", category: "fn_reduction", priority: "MEDIUM", confidence_impact: 0.15, condition: _fn_obfuscated_contact, reason: "Message uses obfuscated contact information to avoid detection. Increasing scam confidence." },
  { rule_id: "FN-010", description: "Digital arrest / authority impersonation scam", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.25, condition: _fn_digital_arrest_scam, reason: "Message impersonates law enforcement or judicial authority with arrest/custody threats. Classic digital arrest scam pattern. Increasing scam confidence." },
  { rule_id: "FN-011", description: "Romance / sweetheart scam", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_romance_scam, reason: "Message uses affection language combined with money requests. Classic romance scam pattern. Increasing scam confidence." },
  { rule_id: "FN-012", description: "Job scam with upfront fees", category: "fn_reduction", priority: "HIGH", confidence_impact: 0.20, condition: _fn_job_scam, reason: "Message offers employment but requires upfront fees (training bond, registration). Classic job scam pattern. Increasing scam confidence." }
];

function _compute_fp_adjustment(analysis) {
  let total_impact = 0;
  const applied = [];
  for (const rule of FP_RULES) {
    try {
      if (rule.condition(analysis)) {
        const impact_points = Math.round(Math.abs(rule.confidence_impact) * 100 * 0.70);
        total_impact += impact_points;
        applied.push({ rule_id: rule.rule_id, description: rule.description, category: rule.category, priority: rule.priority, impact: -impact_points, reason: rule.reason });
      }
    } catch(e) {}
  }
  return { adjustment: Math.min(total_impact, 40), applied };
}

function _compute_fn_adjustment(analysis) {
  let total_impact = 0;
  const applied = [];
  for (const rule of FN_RULES) {
    try {
      if (rule.condition(analysis)) {
        const impact_points = Math.round(Math.abs(rule.confidence_impact) * 100 * 0.70);
        total_impact += impact_points;
        applied.push({ rule_id: rule.rule_id, description: rule.description, category: rule.category, priority: rule.priority, impact: impact_points, reason: rule.reason });
      }
    } catch(e) {}
  }
  return { adjustment: Math.min(total_impact, 40), applied };
}

function _adjust_assessment_score(original_score, fp_adjustment, fn_adjustment) {
  return Math.max(0, Math.min(original_score + fn_adjustment - fp_adjustment, 100));
}

function _map_confidence(assessment_score, has_conflict) {
  if (assessment_score >= 85 && !has_conflict) return CONFIDENCE_HIGH;
  if (assessment_score >= 65) return CONFIDENCE_HIGH;
  if (assessment_score >= 40) return CONFIDENCE_MEDIUM;
  return CONFIDENCE_LOW;
}

function _check_decision_stability(analysis) {
  const concerns = [];
  const assessment_score = analysis.assessment_score || 0;
  const confidence = analysis.confidence || 0.0;
  const band_boundaries = [20, 40, 65, 85];
  for (const boundary of band_boundaries) {
    if (Math.abs(assessment_score - boundary) <= 3) {
      concerns.push("Assessment score (" + assessment_score + ") is within 3 points of decision boundary (" + boundary + "). Small wording changes could alter classification.");
    }
  }
  if (confidence > 0.45 && confidence < 0.55) {
    concerns.push("ML confidence (" + confidence.toFixed(2) + ") is near the 0.5 decision threshold. Minor input variations could flip the prediction.");
  }
  return { stable: concerns.length === 0, concerns };
}

function _build_refinement_summary(applied_fp, applied_fn, stable) {
  const parts = [];
  if (applied_fp.length > 0) parts.push("FP reduction: " + applied_fp.map(r => r.rule_id).join(", "));
  if (applied_fn.length > 0) parts.push("FN reduction: " + applied_fn.map(r => r.rule_id).join(", "));
  if (!stable) parts.push("Decision stability concern flagged");
  if (parts.length === 0) return "No refinement rules triggered. Assessment stands.";
  return "Refinement applied: " + parts.join("; ") + ".";
}

function refine(analysis, assessment) {
  const original_prediction = analysis.prediction || ML_LABEL_SAFE;
  const original_score = assessment.assessment_score || 0;
  const { adjustment: fp_adjustment, applied: applied_fp } = _compute_fp_adjustment(analysis);
  const { adjustment: fn_adjustment, applied: applied_fn } = _compute_fn_adjustment(analysis);

  const refined_score = _adjust_assessment_score(original_score, fp_adjustment, fn_adjustment);
  const has_conflict = (analysis.conflicting_evidence || []).length > 0;
  const refined_confidence = _map_confidence(refined_score, has_conflict);

  let refined_prediction = original_prediction;
  if (fp_adjustment >= 15 && fn_adjustment === 0 && original_prediction === ML_LABEL_SCAM && refined_score < 40) {
    refined_prediction = ML_LABEL_SAFE;
  }
  if (fn_adjustment >= 15 && fp_adjustment === 0 && original_prediction === ML_LABEL_SAFE && refined_score >= 15) {
    refined_prediction = ML_LABEL_SCAM;
  }

  const { stable, concerns } = _check_decision_stability(analysis);
  const summary = _build_refinement_summary(applied_fp, applied_fn, stable);

  return { refined_prediction, refined_assessment_score: refined_score, refined_confidence, stable, concerns, summary, applied_fp, applied_fn };
}

// =============================================================================
// TACTIC EXPLAINERS (prebunking)
// =============================================================================

function getMatchedTactics(indicators, text) {
  const matched = [];
  const seen = new Set();
  const lower = (text || '').toLowerCase();
  for (const ind of indicators || []) {
    const entry = tacticExplain[ind];
    if (entry && !seen.has(entry.tactic)) {
      seen.add(entry.tactic);
      matched.push({ trigger: ind, tactic: entry.tactic, explainer: entry.explainer });
    }
  }
  // Heuristic: surface Digital Arrest as distinct tactic when government impersonation + arrest language appears,
  // even if not already covered by the indicator set (covers the 8 required tactics explicitly)
  if ((lower.includes('digital arrest') || lower.includes('cbi') || lower.includes('ed ') || lower.includes('warrant')) && lower.includes('video call')) {
    const entry = tacticExplain['Digital Arrest'];
    if (entry && !seen.has(entry.tactic)) {
      seen.add(entry.tactic);
      matched.push({ trigger: 'Digital Arrest', tactic: entry.tactic, explainer: entry.explainer });
    }
  }
  // Screen-share / remote-access is often flagged as Customer Care Impersonation; ensure explicit tactic if those keywords appear
  if ((lower.includes('anydesk') || lower.includes('teamviewer') || lower.includes('screen share') || lower.includes('remote access')) ) {
    const entry = tacticExplain['Customer Care Impersonation'];
    if (entry && !seen.has(entry.tactic)) {
      seen.add(entry.tactic);
      matched.push({ trigger: 'Customer Care Impersonation', tactic: entry.tactic, explainer: entry.explainer });
    }
  }
  return matched;
}

// =============================================================================
// MAIN PIPELINE
// =============================================================================

function analyzeText(text) {
  if (!text || typeof text !== 'string') {
    return { risk_level: SEVERITY_VERY_LOW, scam_category: UNKNOWN_CATEGORY, prediction: ML_LABEL_SAFE, confidence: 0, rule_score: 0, rule_label: RISK_LOW, reasons: [], detected_indicators: [], matched_tactics: [], assessment_score: 0, refined_assessment_score: 0 };
  }

  // Step 1: ML prediction
  const features = vectorizer.transform(text);
  const mlResult = model.predict(features);
  const prediction = mlResult.label;
  const confidence = mlResult.confidence;

  // Step 2: Rules
  const rulesResult = analyze_message(text);
  const rule_score = rulesResult.risk_score;
  const rule_label = rulesResult.risk_label;
  const reasons = rulesResult.reasons;

  // Step 3: Explanation
  const explanation_input = { prediction, confidence, rule_score, rule_label, reasons };
  const explanation = generate_explanation(text, explanation_input);

  // Step 4: Intelligence
  const intel = intelligence_analyze(text);

  // Step 5: Evidence
  const evidence_input = {
    prediction, confidence, rule_score, rule_label, reasons,
    detected_indicators: explanation.detected_indicators,
    scam_category: explanation.scam_category,
    entities: intel.entities,
    entity_summary: intel.entity_summary,
    entity_risk: intel.entity_risk
  };
  const evidence = build_evidence(evidence_input);

  // Step 6: Assessment
  const assessment_input = {
    prediction, confidence, rule_score, rule_label,
    decision_score: evidence.decision_score,
    detected_indicators: explanation.detected_indicators,
    scam_category: explanation.scam_category,
    entity_risk: intel.entity_risk,
    supporting_evidence: evidence.supporting_evidence,
    conflicting_evidence: evidence.conflicting_evidence,
    confidence_breakdown: evidence.confidence_breakdown
  };
  const assessmentResult = assess(assessment_input);

  // Step 7: Refinement
  const refinement_input = {
    prediction, confidence, rule_score, rule_label,
    detected_indicators: explanation.detected_indicators,
    scam_category: explanation.scam_category,
    entities: intel.entities,
    reasons,
    _original_text: text,
    conflicting_evidence: evidence.conflicting_evidence,
    assessment_score: assessmentResult.assessment_score
  };
  const refinement = refine(refinement_input, assessmentResult);

  const matched_tactics = getMatchedTactics(explanation.detected_indicators, text);

  return {
    risk_level: explanation.risk_level,
    scam_category: explanation.scam_category,
    prediction,
    confidence,
    rule_score,
    rule_label,
    reasons,
    detected_indicators: explanation.detected_indicators,
    matched_tactics,
    threats: explanation.threats,
    recommended_actions: explanation.recommended_actions,
    summary: explanation.summary,
    confidence_reason: explanation.confidence_reason,
    entities: intel.entities,
    entity_summary: intel.entity_summary,
    entity_risk: intel.entity_risk,
    decision_score: evidence.decision_score,
    supporting_evidence: evidence.supporting_evidence,
    conflicting_evidence: evidence.conflicting_evidence,
    evidence_confidence_breakdown: evidence.confidence_breakdown,
    evidence_risk_breakdown: evidence.risk_breakdown,
    assessment_score: assessmentResult.assessment_score,
    assessment_band: assessmentResult.assessment_band,
    assessment_confidence: assessmentResult.assessment_confidence,
    review_required: assessmentResult.review_required,
    refined_prediction: refinement.refined_prediction,
    refined_assessment_score: refinement.refined_assessment_score,
    refined_confidence: refinement.refined_confidence,
    decision_stable: refinement.stable,
    stability_concerns: refinement.concerns,
    refinement_summary: refinement.summary
  };
}

export { analyzeText };
export default { analyzeText };
