import os
import random
import pandas as pd

# Set random seed for reproducibility
random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_datasets")
os.makedirs(OUT_DIR, exist_ok=True)

# ==============================================================================
# 1. E-Commerce & Online Retail Complaints Dataset (1,200 rows)
# ==============================================================================
ecommerce_categories = {
    "Delivery & Shipping Delays": [
        "My order {order_id} was supposed to arrive {duration} ago. Tracking still says pending at sorting hub in {city}!",
        "Express delivery promised 2-day delivery for order {order_id}, but it has been {duration} and no courier has shown up.",
        "Package {order_id} shows delivered by courier in {city}, but I checked my porch and security camera and nothing is there!",
        "Severe shipping delay on order {order_id}. I paid an extra {amount} for priority dispatch and it is completely missing.",
        "Driver marked order {order_id} as delivery attempted, but I was sitting right by the front door all day in {city}!"
    ],
    "Damaged & Defective Items": [
        "Received my electronic order {order_id} completely broken. The display screen is cracked and won't turn on.",
        "Opened parcel {order_id} and the perfume bottle leaked everywhere. The entire box was crushed during transit.",
        "The blender I bought for {amount} stopped working after 10 minutes with burning smell and smoke coming out.",
        "Quality is appalling. Received a damaged leather bag with ripped stitching on handle for order {order_id}.",
        "Item arrived shattered into pieces inside bubble wrap. Package was handled with zero care by carrier."
    ],
    "Refund & Return Discrepancies": [
        "Returned parcel {order_id} {duration} ago with return tracking number. Where is my refund of {amount}?",
        "Your customer support promised my refund of {amount} would be credited within 48 hours, still nothing in my bank account.",
        "Customer service deducted a {amount} restocking fee when I returned an incorrect shoe size that was your fault!",
        "I sent back the jacket for order {order_id} and the warehouse confirmed receipt, but the return portal still says pending inspection.",
        "Where is my money? You cancelled my order {order_id} without my consent and withheld the {amount} charge!"
    ],
    "Wrong Item Sent": [
        "I ordered an XL blue winter jacket but you shipped a medium green dress for order {order_id}!",
        "Completely wrong product received! Ordered wireless headphones worth {amount} and received cheap plastic phone cases.",
        "Received someone else's order! Packing slip inside box {order_id} has a different customer name and address in {city}.",
        "Ordered a set of 4 ceramic plates and only received 2 bowls. Half my package is missing.",
        "Wrong shoe model sent. I paid {amount} for running shoes and got casual slip-ons."
    ],
    "Subscription & Overcharging": [
        "Charged {amount} for Prime annual membership renewal after I explicitly cancelled auto-renew last month!",
        "Double charged on my credit card for order {order_id}. You billed me {amount} twice for the same transaction.",
        "Promo code SAVE20 was applied at checkout but invoice shows full price without the 20% discount applied.",
        "Unauthorized recurring charge of {amount} on my statement under billing descriptor ECOM-SUBSCRIPTION.",
        "Why was I billed an unexpected international transaction fee of {amount} on a domestic order?"
    ]
}

ecom_anomalies = [
    "Sub-quantum lattice entanglement across peripheral nano-assemblies detected in optical matrix 0x9F.",
    "Bilateral matrix orbital decay vector calibration mismatch on terminal gyro compass.",
    "Cosmic ray muon scintillation event disrupted CMOS sensor shift register.",
    "Hyper-frequency Doppler shift on waveguide reflector plate alpha.",
    "Piezoelectric actuator impedance resonance mismatch in sub-micron vacuum chamber."
]

def generate_ecommerce_dataset(n_rows=1200):
    rows = []
    cities = ["New York", "Chicago", "Dallas", "Atlanta", "Seattle", "Los Angeles", "Miami", "Boston"]
    durations = ["3 days", "5 days", "10 days", "2 weeks", "48 hours", "14 days"]
    amounts = ["$24.99", "$49.50", "$89.00", "$149.99", "$280.00", "$450.00", "$65.00"]
    
    cat_keys = list(ecommerce_categories.keys())
    per_cat = (n_rows - 20) // len(cat_keys)
    
    comp_id = 1000
    for cat in cat_keys:
        templates = ecommerce_categories[cat]
        for _ in range(per_cat):
            t = random.choice(templates)
            text = t.format(
                order_id=f"ORD-{random.randint(10000, 99999)}",
                duration=random.choice(durations),
                city=random.choice(cities),
                amount=random.choice(amounts)
            )
            rows.append({
                "complaint_id": f"ECOM-{comp_id}",
                "text": text,
                "domain": "E-Commerce",
                "category": cat
            })
            comp_id += 1
            
    # Add anomalies
    for anomaly_text in ecom_anomalies * 4:
        rows.append({
            "complaint_id": f"ECOM-{comp_id}",
            "text": anomaly_text,
            "domain": "E-Commerce",
            "category": "Technical Anomaly / Outlier"
        })
        comp_id += 1
        
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "ecommerce_customer_complaints.csv")
    df.to_csv(path, index=False)
    print(f"Generated E-Commerce dataset: {path} with {len(df)} rows.")
    return path


# ==============================================================================
# 2. Banking & FinTech Complaints Dataset (1,200 rows)
# ==============================================================================
banking_categories = {
    "Credit Card Fraud & Unauthorized Charges": [
        "Fraud alert! Unauthorized credit card charge of {amount} from merchant in {city} that I never visited.",
        "Someone used my debit card number to buy electronics online for {amount}. Please block card and initiate chargeback.",
        "Suspicious international charge of {amount} appearing on my credit statement under reference {txn_id}.",
        "My wallet was stolen in {city} and thief made {amount} in contactless purchases before I could lock the mobile app.",
        "Unrecognized POS terminal charge of {amount} on my card. I demand immediate provisional credit."
    ],
    "ATM & Cash Withdrawal Failures": [
        "ATM in {city} failed to dispense cash, but my checking account was debited {amount}! Trace ID {txn_id}.",
        "Machine swallowed my debit card at the branch ATM on Main Street after showing out of service error.",
        "Requested {amount} cash withdrawal at ATM; machine only gave me $40 but debited the full {amount} from my balance.",
        "ATM terminal timed out during cash deposit. The machine took my {amount} envelope without printing a receipt.",
        "Emergency cash disbursement request failed at ATM terminal {txn_id}. I am stranded with zero cash."
    ],
    "Wire Transfers & ACH Delays": [
        "Sent international wire transfer of {amount} {duration} ago to overseas supplier, funds still not credited!",
        "ACH direct deposit from my employer has not posted to my account. Reference number {txn_id}.",
        "Outgoing wire transfer of {amount} is stuck on pending status for {duration} with no explanation.",
        "Recipient bank claims wire {txn_id} was rejected due to intermediary routing error, but funds were never returned to my account.",
        "Same-day wire fee of {amount} was charged but wire took 4 business days to clear!"
    ],
    "Loan & Mortgage Processing": [
        "Mortgage escrow calculation is totally incorrect! You increased my monthly payment by {amount} without justification.",
        "Submitted auto loan refinancing paperwork {duration} ago. Loan officer never answers emails or phone calls.",
        "Unfair late payment penalty of {amount} assessed on mortgage when payment was submitted before the 15th grace period.",
        "Student loan interest capitalization was calculated at incorrect rates following repayment plan change.",
        "Payoff quote request for vehicle loan account {txn_id} has been ignored for {duration}."
    ],
    "Mobile Banking & Account Access": [
        "Mobile banking app keeps giving error 403 when trying to log in. Face ID and password both fail.",
        "Locked out of online banking because SMS OTP verification codes are not arriving on my registered mobile number.",
        "Online banking balance showing negative balance due to duplicate pending authorization holds.",
        "Cannot add debit card to Apple Pay / Google Wallet. Bank system says verification unavailable.",
        "Biometric login glitch in iOS app version 4.2 causes immediate crash whenever viewing transaction history."
    ]
}

def generate_banking_dataset(n_rows=1200):
    rows = []
    cities = ["New York", "Chicago", "Charlotte", "San Francisco", "Miami", "Dallas", "Phoenix", "London"]
    durations = ["24 hours", "3 business days", "5 days", "1 week", "2 weeks"]
    amounts = ["$150.00", "$320.50", "$750.00", "$1,200.00", "$2,500.00", "$4,800.00", "$85.00"]
    
    cat_keys = list(banking_categories.keys())
    per_cat = (n_rows - 20) // len(cat_keys)
    
    comp_id = 2000
    for cat in cat_keys:
        templates = banking_categories[cat]
        for _ in range(per_cat):
            t = random.choice(templates)
            text = t.format(
                txn_id=f"TXN-{random.randint(100000, 999999)}",
                duration=random.choice(durations),
                city=random.choice(cities),
                amount=random.choice(amounts)
            )
            rows.append({
                "complaint_id": f"BANK-{comp_id}",
                "text": text,
                "domain": "Banking & FinTech",
                "category": cat
            })
            comp_id += 1
            
    # Add anomalies
    for anomaly_text in ecom_anomalies * 4:
        rows.append({
            "complaint_id": f"BANK-{comp_id}",
            "text": anomaly_text,
            "domain": "Banking & FinTech",
            "category": "Technical Anomaly / Outlier"
        })
        comp_id += 1
        
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "banking_fintech_complaints.csv")
    df.to_csv(path, index=False)
    print(f"Generated Banking dataset: {path} with {len(df)} rows.")
    return path


# ==============================================================================
# 3. Telecom & Internet Service Provider Complaints (1,200 rows)
# ==============================================================================
telecom_categories = {
    "Broadband Outage & Slow Speed": [
        "Complete fiber internet blackout in {city} neighborhood for the past {duration}! Router power light is red.",
        "Paying {amount} monthly for 1 Gbps gigabit fiber, but speed test only shows 12 Mbps download and high packet loss.",
        "Internet drops connection every 15 minutes during Zoom work calls. Technician ticket {ticket_id} still unresolved.",
        "Fiber ONT box LOS red light blinking constantly. Work from home is impossible without connection.",
        "Massive latency spike and ping of 450ms when playing online games or streaming 4K video."
    ],
    "Cellular 5G Signal & Dropped Calls": [
        "Zero 5G cellular coverage inside my house in {city}. Emergency calls only and calls drop every 2 minutes.",
        "Ever since the recent tower upgrade in area code 90210, mobile data speed is slower than 3G.",
        "Outgoing phone calls fail with call failed error code 18 on iPhone 15 Pro Max.",
        "Text messages and SMS verification codes fail to send or receive on cellular network.",
        "Voicemail notifications arrive 3 days late. Missed urgent hospital call due to network silence."
    ],
    "Billing Shock & Hidden Charges": [
        "Shocked to see a {amount} bill this month when my contracted plan rate is only $60! Account {ticket_id}.",
        "Charged {amount} for international data roaming while my phone was connected to airport Wi-Fi!",
        "Mystery charge of {amount} for equipment rental fee when I bought and supplied my own DOCSIS router.",
        "Cancelled service {duration} ago, yet auto-pay deducted another {amount} from my checking account.",
        "Paper billing fee and regulatory recovery fee increased without prior 30-day notice."
    ],
    "SIM Porting & eSIM Activation": [
        "Transferred my phone number from competitor {duration} ago; old carrier disconnected but your eSIM won't activate!",
        "Porting request {ticket_id} stuck in carrier limbo. My phone number is completely unreachable for business.",
        "QR code for eSIM activation returned invalid profile error. Stranded with no cellular reception.",
        "SIM card swap protection failed! I received an email saying my number was transferred without my authorization.",
        "Physical SIM card replacement ordered {duration} ago has not arrived in mail."
    ],
    "Hardware & Technician Appointments": [
        "Broadband technician failed to show up for scheduled appointment window in {city}. Waited 5 hours for nothing!",
        "Wi-Fi gateway router overheats and reboots every hour. Unit is hot to the touch and smells of burning plastic.",
        "Field technician replaced the external drop cable but left exposed fiber wiring hanging across my front lawn.",
        "Returned the old modem via UPS with tracking receipt, yet you billed me {amount} unreturned equipment fee!",
        "Set-top TV box remote control stopped pairing with television receiver {ticket_id}."
    ]
}

def generate_telecom_dataset(n_rows=1200):
    rows = []
    cities = ["Dallas", "Chicago", "Denver", "Seattle", "Austin", "San Jose", "Orlando", "Philadelphia"]
    durations = ["24 hours", "48 hours", "3 days", "5 days", "1 week"]
    amounts = ["$120.00", "$185.50", "$250.00", "$340.00", "$89.99", "$420.00"]
    
    cat_keys = list(telecom_categories.keys())
    per_cat = (n_rows - 20) // len(cat_keys)
    
    comp_id = 3000
    for cat in cat_keys:
        templates = telecom_categories[cat]
        for _ in range(per_cat):
            t = random.choice(templates)
            text = t.format(
                ticket_id=f"TKT-{random.randint(100000, 999999)}",
                duration=random.choice(durations),
                city=random.choice(cities),
                amount=random.choice(amounts)
            )
            rows.append({
                "complaint_id": f"TEL-{comp_id}",
                "text": text,
                "domain": "Telecom & ISP",
                "category": cat
            })
            comp_id += 1
            
    # Add anomalies
    for anomaly_text in ecom_anomalies * 4:
        rows.append({
            "complaint_id": f"TEL-{comp_id}",
            "text": anomaly_text,
            "domain": "Telecom & ISP",
            "category": "Technical Anomaly / Outlier"
        })
        comp_id += 1
        
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "telecom_isp_complaints.csv")
    df.to_csv(path, index=False)
    print(f"Generated Telecom dataset: {path} with {len(df)} rows.")
    return path


if __name__ == "__main__":
    generate_ecommerce_dataset()
    generate_banking_dataset()
    generate_telecom_dataset()
    print("All datasets generated successfully!")
