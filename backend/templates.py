import re
import os
import json
import random
import uuid
import logging
import requests

logger = logging.getLogger("templates_rag")

# Preset test cases demonstrating all decision paths
PRESET_COMPLAINTS = [
    {
        "id": "case-1",
        "category": "Flight Delay (Standard Query)",
        "expected_decision": "AI",
        "text": "Flight UA458 from Chicago is delayed by 45 minutes. Can you provide the updated departure time and gate number?",
        "description": "Routine flight delay query with neutral sentiment and high similarity to the flight delay cluster."
    },
    {
        "id": "case-2",
        "category": "Baggage Claim Status",
        "expected_decision": "AI",
        "text": "My checked bag has not arrived on carousel 4 after flight 892. Where can I track my delayed luggage claim?",
        "description": "Standard baggage tracking inquiry matching the baggage cluster with high similarity."
    },
    {
        "id": "case-3",
        "category": "Severe Outrage & Hostile Service",
        "expected_decision": "HUMAN",
        "text": "Disgusting treatment! Stranded my elderly mother for 14 hours with no food, no water, and the rude supervisor laughed in our faces! Absolute nightmare!",
        "description": "Severe negative sentiment (VADER compound < -0.6) immediately triggers escalation to a human supervisor."
    },
    {
        "id": "case-4",
        "category": "DBSCAN Anomaly / Unseen Topic",
        "expected_decision": "HUMAN",
        "text": "Quantum telemetry sub-carrier oscillation frequencies on payload transponder 0x4B require optical azimuth alignment.",
        "description": "Out-of-domain vocabulary with neutral sentiment; DBSCAN marks it as an outlier anomaly requiring human specialist triage."
    },
    {
        "id": "case-5",
        "category": "Vague / Ambiguous Complaint",
        "expected_decision": "HUMAN",
        "text": "Something seemed strange about the whole process yesterday.",
        "description": "Vague neutral text with low cluster similarity (< threshold); safely routes to human support."
    },
    {
        "id": "case-6",
        "category": "Customer Compliment",
        "expected_decision": "AI",
        "text": "Huge thank you to Captain Dave and the cabin crew on flight 214! You turned a stressful day into a wonderfully comfortable journey!",
        "description": "Positive sentiment inquiry triggering an appreciative automated response."
    }
]

# Multi-Domain Customer Service Policies for RAG Injection
AIRLINE_POLICIES = {
    "delays_cancellations": {
        "title": "Service Disruption & Delay Resolution Policy",
        "summary": "For controllable service delays or cancellations, customers are provided immediate priority rebooking or full refunds without penalty, along with interim support credits.",
        "citation": "Consumer Protection Standards §240.4"
    },
    "baggage_claims": {
        "title": "Mishandled Property & Baggage Resolution Policy",
        "summary": "Delayed or mishandled items receive accelerated tracking. For delays exceeding 24 hours, interim reimbursement is provided up to standard carrier liability guidelines.",
        "citation": "Property Resolution Standards 14 CFR Part 254"
    },
    "ticketing_reservations": {
        "title": "24-Hour Flexible Booking & Ticketing Policy",
        "summary": "Orders or reservations can be adjusted or cancelled within 24 hours without penalty fees, with instant digital confirmation and zero change fees.",
        "citation": "Consumer Protection Fair Booking Standards"
    },
    "customer_service": {
        "title": "Customer Service Commitment & Escalation SLA",
        "summary": "Standard customer service inquiries receive first-touch resolution within 2 hours. High-frustration or escalated complaints trigger immediate senior supervisor review with guaranteed customer callback within 30 minutes.",
        "citation": "Customer Service Quality Standards ISO-10002"
    },
    "in_flight_experience": {
        "title": "In-Flight Comfort & Amenities Guarantee",
        "summary": "If standard cabin amenities such as in-flight Wi-Fi, personal audio/video screens, or pre-reserved seat categories fail during a flight, passengers are issued compensatory travel credits ($50–$150) or mileage refunds within 48 hours of claim submission.",
        "citation": "Cabin Service Standards & Quality Assurance Manual"
    },
    "software_digital": {
        "title": "Digital Platform, Mobile App & Account Security SLA",
        "summary": "Reported software bugs, update regressions, or mobile session failures receive accelerated technical triage with immediate troubleshooting steps and account recovery verification.",
        "citation": "Digital Service Performance Standards QA-401"
    },
    "hardware_billing": {
        "title": "Device Warranty, Billing & Network Service Policy",
        "summary": "Billing disputes, network downtime, or device power/hardware issues are reviewed with immediate credit adjustments and technical diagnostics.",
        "citation": "Telecommunications & Device Fair Practice Code"
    }
}


def extract_entities(text: str) -> dict:
    """
    Extracts key operational entities from complaint text:
    - Flight numbers (e.g. UA458, Flight 892, VX358)
    - Booking / PNR codes (e.g. 6-character alphanumeric)
    - Monetary amounts (e.g. $250, $30)
    - Airports / Locations (e.g. SFO, LAX, Chicago, Paris)
    - Time / Duration mentions (e.g. 14 hours, 45 minutes)
    """
    entities = {
        "flight_number": None,
        "booking_reference": None,
        "monetary_amount": None,
        "locations": [],
        "duration": None
    }
    
    # 1. Flight Number: Carrier code + digits or "flight 123"
    flight_match = re.search(r'\b(?:flight\s*#?|flt\s*#?|[A-Z]{2}\s*|[A-Z]\d\s*)(\d{2,4})\b', text, re.IGNORECASE)
    if flight_match:
        entities["flight_number"] = f"FLT-{flight_match.group(1)}"
    else:
        # Check standard airline prefix like UA458, VX358
        prefix_match = re.search(r'\b([A-Z]{2}\d{2,4})\b', text)
        if prefix_match:
            entities["flight_number"] = prefix_match.group(1).upper()

    # 2. Monetary amounts ($XX or XX dollars)
    money_match = re.search(r'(?:\$\s*\d+(?:\.\d{2})?|\b\d+\s*(?:dollars|usd)\b)', text, re.IGNORECASE)
    if money_match:
        entities["monetary_amount"] = money_match.group(0).upper()

    # 3. Durations (e.g. 14 hours, 45 minutes)
    duration_match = re.search(r'\b(\d+\s*(?:hour|hr|minute|min|day)s?)\b', text, re.IGNORECASE)
    if duration_match:
        entities["duration"] = duration_match.group(1).lower()

    # 4. Known Airports & major destinations
    KNOWN_PLACES = [
        "SFO", "LAX", "JFK", "ORD", "DFW", "ATL", "BOS", "EWR", "MIA", "SEA", "DEN",
        "Chicago", "New York", "San Francisco", "Los Angeles", "Boston", "Cancun", "Paris", "London", "Dallas", "Atlanta"
    ]
    found_places = []
    for place in KNOWN_PLACES:
        if re.search(rf'\b{re.escape(place)}\b', text, re.IGNORECASE):
            found_places.append(place.upper() if len(place) <= 3 else place.title())
    entities["locations"] = list(dict.fromkeys(found_places))[:3]

    # 5. PNR / Booking code (e.g. 6 capital letters/numbers)
    pnr_match = re.search(r'\b([A-Z0-9]{6})\b', text)
    if pnr_match and pnr_match.group(1) not in ["CANCEL", "UNITED", "VIRGIN", "JETBLU", "FLIGHT"]:
        entities["booking_reference"] = pnr_match.group(1)

    return entities


def select_policy(cluster_name: str, text: str) -> dict:
    """Retrieves relevant policy dynamically based on cluster topic and complaint content."""
    cluster_lower = cluster_name.lower()
    text_lower = text.lower()
    
    # Software, App, OS, Digital Service
    if any(w in cluster_lower or w in text_lower for w in ["app", "ios", "iphone", "android", "software", "update", "battery", "crash", "download", "login", "bug", "dm", "message"]):
        return AIRLINE_POLICIES["software_digital"]
    # Telecommunications, Hardware, Internet & Network
    elif any(w in cluster_lower or w in text_lower for w in ["internet", "wifi", "network", "bill", "billing", "store", "device", "connection", "broadband"]):
        return AIRLINE_POLICIES["hardware_billing"]
    # Baggage / Shipping & Deliveries
    elif any(w in cluster_lower or w in text_lower for w in ["bag", "luggage", "suitcase", "lost", "carousel", "delivery", "item", "package"]):
        return AIRLINE_POLICIES["baggage_claims"]
    # Delays, Cancellations, Flight disruptions
    elif any(w in cluster_lower or w in text_lower for w in ["delay", "cancel", "late", "schedule", "divert", "flight", "terminal", "gate"]):
        return AIRLINE_POLICIES["delays_cancellations"]
    # Bookings, Reservations, Payments
    elif any(w in cluster_lower or w in text_lower for w in ["ticket", "book", "reservation", "change", "refund", "fee", "card", "account"]):
        return AIRLINE_POLICIES["ticketing_reservations"]
    # In-Flight or Product Experience
    elif any(w in cluster_lower or w in text_lower for w in ["seat", "comfort", "screen", "cabin", "food"]):
        return AIRLINE_POLICIES["in_flight_experience"]
        
    return AIRLINE_POLICIES["customer_service"]


def generate_rag_response(
    decision: str,
    reason: str,
    cluster_name: str,
    sentiment: str,
    sentiment_scores: dict,
    similarity: float,
    is_anomaly: bool,
    text: str,
    ticket_id: str
) -> dict:
    """
    Dynamic LLM / RAG Response Generator:
    1. Extracts operational entities (IDs, Amounts, Locations, Durations).
    2. Retrieves relevant domain policies.
    3. Crafts a tailored, personalized, empathetic official communication.
    """
    entities = extract_entities(text)
    policy = select_policy(cluster_name, text)
    
    is_flight = bool(entities["flight_number"] or any(w in cluster_name.lower() or w in text.lower() for w in ["flight", "airline", "airport", "gate", "boarding", "luggage"]))
    is_tech = any(w in cluster_name.lower() or w in text.lower() for w in ["app", "ios", "iphone", "android", "software", "update", "battery", "crash", "dm", "message", "device"])

    flight_str = f" regarding {entities['flight_number']}" if entities["flight_number"] else ""
    location_str = f" ({' → '.join(entities['locations'])})" if len(entities['locations']) >= 2 else (f" at {entities['locations'][0]}" if entities['locations'] else "")
    duration_str = f" of {entities['duration']}" if entities['duration'] else ""

    customer_greeting = "Dear Traveler," if is_flight else "Dear Valued Customer,"
    service_label = "travel experience" if is_flight else ("digital service experience" if is_tech else "customer experience")
    dept_label = "Flight & Airport Operations Desk" if is_flight else ("Digital & Technical Support Services" if is_tech else "Customer Care Priority Directorate")
    signoff_label = "Thank you for flying with us,\nCustomer Operations Team" if is_flight else "Best regards,\nCustomer Support & Care Team"

    # Subject line
    if decision == "HUMAN":
        subject = f"[PRIORITY ESCALATION] Ticket #{ticket_id} - Urgent Case Review{flight_str}"
    elif sentiment == "Positive":
        subject = f"Thank You for Your Feedback! (Ref #{ticket_id})"
    else:
        subject = f"[Official Resolution] Assistance Regarding Your Inquiry #{ticket_id}{flight_str}"

    # Check if local Ollama LLM is running
    ollama_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3")
    
    ollama_response = None
    try:
        prompt = (
            f"You are an empathetic customer support manager. "
            f"Customer inquiry: '{text}'. "
            f"Decision: {decision}. Cluster: {cluster_name}. Sentiment: {sentiment}. "
            f"Extracted entities: {entities}. Policy to cite: {policy['title']} - {policy['summary']}. "
            f"Ticket: #{ticket_id}. Write a polite, empathetic customer email."
        )
        resp = requests.post(
            ollama_url,
            json={"model": ollama_model, "prompt": prompt, "stream": False},
            timeout=0.8
        )
        if resp.status_code == 200:
            data = resp.json()
            if "response" in data and len(data["response"].strip()) > 30:
                ollama_response = data["response"].strip()
                logger.info("Successfully generated dynamic reply via local Ollama LLM!")
    except Exception:
        pass

    if ollama_response:
        body = ollama_response
        engine = f"Ollama Local LLM ({ollama_model})"
    else:
        engine = "Policy-Augmented Contextual Engine (RAG)"
        
        # Build customized, personalized, policy-aware message
        if decision == "HUMAN":
            if sentiment_scores.get("compound", 0) <= -0.50 or sentiment_scores.get("neg", 0) >= 0.35:
                body = (
                    f"{customer_greeting}\n\n"
                    f"We have received your urgent message regarding your recent {service_label}{flight_str}{location_str}. "
                    f"Please accept our deepest apologies for the extreme frustration and distress this has caused. We hold our service to the highest standards, and it is clear we failed to meet them on this occasion.\n\n"
                    f"In accordance with our {policy['title']}, this case has been immediately escalated to our Senior Duty Manager under Ticket #{ticket_id}. "
                    f"Our priority care team is currently reviewing the operational records to resolve this matter. "
                    f"A senior supervisor has been assigned to contact you directly within 15–30 minutes with an immediate corrective resolution.\n\n"
                    f"Sincerely,\n"
                    f"{dept_label}\n"
                    f"Incident Reference: #{ticket_id}"
                )
            elif is_anomaly:
                body = (
                    f"{customer_greeting}\n\n"
                    f"Thank you for contacting customer support. We have received your inquiry under Reference #{ticket_id}.\n\n"
                    f"Our automated diagnostic system has identified specialized, non-standard requirements in your message that require manual evaluation by our Specialized Operations & Technical Support Team. "
                    f"We have placed your case in our Priority Specialist Queue to ensure every detail is handled accurately and thoroughly.\n\n"
                    f"A specialist will review your request and follow up directly via your email or registered contact on file.\n\n"
                    f"Best regards,\n"
                    f"Specialized Support Operations Desk\n"
                    f"Reference: #{ticket_id}"
                )
            else:
                body = (
                    f"{customer_greeting}\n\n"
                    f"Thank you for reaching out to us regarding your {service_label}{flight_str}{location_str}.\n\n"
                    f"To ensure your specific concerns receive the detailed, personalized care they deserve, your inquiry has been routed to our dedicated Customer Solutions Team (Ticket #{ticket_id}). "
                    f"Our team operates under our {policy['title']}, ensuring every case receives comprehensive review and prompt resolution.\n\n"
                    f"An agent has been assigned to your file and will be in touch with you shortly with full details.\n\n"
                    f"Warm regards,\n"
                    f"Customer Experience Team\n"
                    f"Ticket #{ticket_id}"
                )
        elif sentiment == "Positive":
            body = (
                f"{customer_greeting}\n\n"
                f"Thank you so much for taking the time to share your positive experience{flight_str}{location_str}!\n\n"
                f"Nothing makes us happier than hearing that our team made your experience seamless and enjoyable. "
                f"We have formally logged your kind words under Reference #{ticket_id} and forwarded your commendation directly to our leadership and service teams.\n\n"
                f"We look forward to serving you again soon!\n\n"
                f"Warmest regards,\n"
                f"Customer Hospitality & Experience Team\n"
                f"Reference #{ticket_id}"
            )
        else:
            # AI Automated Response with precise policy citation
            body = (
                f"{customer_greeting}\n\n"
                f"Thank you for contacting customer support regarding your inquiry{flight_str}{location_str}{duration_str}. "
                f"We understand how important prompt assistance is, and we are here to assist you immediately.\n\n"
                f"Under our {policy['title']} ({policy['citation']}):\n"
                f"• {policy['summary']}\n\n"
                f"Your request has been registered in our automated tracking network under Reference #{ticket_id}. "
                f"You can also manage your request, track status in real-time, or receive direct assistance through our self-service portal or official mobile channels.\n\n"
                f"If you need further immediate assistance, our 24/7 digital assistant is available at your convenience.\n\n"
                f"{signoff_label}\n"
                f"Case Reference: #{ticket_id}"
            )

    return {
        "email_subject": subject,
        "email_body": body,
        "retrieved_policy": {
            "title": policy["title"],
            "summary": policy["summary"],
            "citation": policy["citation"]
        },
        "extracted_entities": entities,
        "engine_used": engine,
        "ticket_id": ticket_id
    }


def generate_ticket_id() -> str:
    return f"TCK-{random.randint(1000, 9999)}-{uuid.uuid4().hex[:4].upper()}"


def generate_response(
    decision: str,
    reason: str,
    cluster_name: str,
    sentiment: str,
    sentiment_scores: dict,
    similarity: float,
    is_anomaly: bool,
    text: str
) -> str:
    """
    Generates tailored, empathetic response based on decision engine outcome.
    """
    ticket_id = generate_ticket_id()
    cluster_lower = cluster_name.lower()
    
    if decision == "HUMAN":
        # Escalation message with priority assurance
        if "Severe negative" in reason or "negativity" in reason.lower():
            return (
                f"We are deeply sorry for the distressing experience you have had. "
                f"Your complaint has been immediately escalated to our Senior Priority Support Desk under Ticket #{ticket_id}. "
                f"A senior supervisor has been assigned to contact you directly within 15–30 minutes to make things right."
            )
        elif is_anomaly or "Anomaly" in reason:
            return (
                f"Thank you for contacting us. Your request contains non-standard parameters that require specialized human review. "
                f"We have routed your ticket (#{ticket_id}) to our Specialized Technical & Operations Team for manual evaluation."
            )
        else:
            return (
                f"Thank you for reaching out. To ensure your inquiry receives the personalized attention it needs, "
                f"we have assigned this matter to a human customer care representative (Reference Ticket #{ticket_id}). "
                f"An agent will review your inquiry and reply shortly."
            )
    
    # Decision is AI auto-reply
    if sentiment == "Positive":
        is_flight = any(w in cluster_lower or w in text.lower() for w in ["flight", "airline", "fly", "plane", "gate", "crew"])
        if is_flight:
            return (
                f"Thank you so much for your kind words! We are thrilled to hear about your great flight experience. "
                f"We have forwarded your compliments to our operations team and flight crew. Safe travels! (Ref: #{ticket_id})"
            )
        return (
            f"Thank you so much for your kind feedback! We are thrilled to hear you had a great experience with our team. "
            f"We have formally logged your compliments under Reference #{ticket_id} and shared them with our leadership team."
        )
    
    # Cluster-tailored empathetic AI responses
    if any(w in cluster_lower or w in text.lower() for w in ["app", "ios", "iphone", "android", "software", "update", "battery", "crash", "bug"]):
        return (
            f"Thank you for reporting this software issue. Our technical engineering team is actively investigating this behavior. "
            f"Please ensure you are on the latest app release, or try restarting your device session. Reference: #{ticket_id}"
        )
    elif any(w in cluster_lower or w in text.lower() for w in ["dm", "direct message", "message", "send", "inbox"]):
        return (
            f"Thank you for contacting our care team. We have opened Reference #{ticket_id} for you. "
            f"Please verify that your direct message has been sent, and an active specialist will follow up shortly."
        )
    elif any(w in cluster_lower or w in text.lower() for w in ["internet", "wifi", "network", "bill", "billing", "store", "device"]):
        return (
            f"We apologize for the service disruption. Our network operations team is monitoring system availability in real-time. "
            f"Your report has been logged under Reference #{ticket_id} for automated diagnostic review."
        )
    elif any(w in cluster_lower for w in ["delay", "cancel", "schedule", "late", "flight"]):
        return (
            f"We sincerely apologize for the delay and schedule inconvenience. "
            f"Our operations team is monitoring all departure updates in real-time. "
            f"You can view live gate information and rebooking options in our mobile app or web portal. (Reference: #{ticket_id})"
        )
    elif any(w in cluster_lower for w in ["bag", "luggage", "lost", "claim"]):
        return (
            f"We apologize for the trouble with your baggage. "
            f"To track delayed or mishandled luggage in real time, please visit our Baggage Tracking portal "
            f"using your claim tag. Over 90% of delayed bags arrive within 12–24 hours. (Reference: #{ticket_id})"
        )
    elif any(w in cluster_lower for w in ["booking", "ticket", "change", "reservation", "online"]):
        return (
            f"Thank you for reaching out regarding your reservation. "
            f"You can modify dates, select preferences, or view confirmation receipts 24/7 in 'Manage Reservations' on our website. "
            f"A confirmation receipt has also been dispatched to your email on file. (Reference: #{ticket_id})"
        )
    elif any(w in cluster_lower for w in ["phone", "call", "service", "wait", "hold"]):
        return (
            f"We apologize for the wait time you experienced. "
            f"We are actively increasing support capacity. "
            f"Your request has been logged under Reference #{ticket_id}. You can also use our 24/7 self-service chat for instant updates."
        )
    else:
        return (
            f"Thank you for contacting customer support. "
            f"We have logged your request regarding {cluster_name.lower()} under Reference #{ticket_id}. "
            f"Our automated assistant is standing by to help with any additional information you may need."
        )
